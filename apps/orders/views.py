from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
import uuid

from .models import PurchaseOrder, OrderItem, Invoice
from .serializers import PurchaseOrderSerializer, OrderItemSerializer, InvoiceSerializer
from .pdf_generator import generate_order_pdf, generate_invoice_pdf
from apps.inventory.models import InventoryItem, Product
from apps.accounts.models import Company

class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.select_related('buyer_company', 'supplier_company').prefetch_related('items__product', 'invoice').all()
    serializer_class = PurchaseOrderSerializer

    @action(detail=True, methods=['get'])
    def pdf(self, request, pk=None):
        order = self.get_object()
        pdf_content = generate_order_pdf(order)
        filename = f"{order.order_number}.pdf"
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')
        if new_status not in dict(PurchaseOrder.STATUS_CHOICES):
            return Response({'error': f'Invalid status: {new_status}'}, status=status.HTTP_400_BAD_REQUEST)

        old_status = order.status
        order.status = new_status

        # If order is delivered, set actual delivery date and mark received quantities
        if new_status == 'DELIVERED':
            if not order.actual_delivery_date:
                order.actual_delivery_date = timezone.now().date()
            for item in order.items.all():
                item.quantity_received = item.quantity_requested
                item.save()

        # If order is rejected or cancelled, restore deducted stock back to the supplier
        elif new_status in ['REJECTED_BY_SUPPLIER', 'REJECTED_BY_BUYER', 'CANCELLED'] and old_status not in ['REJECTED_BY_SUPPLIER', 'REJECTED_BY_BUYER', 'CANCELLED']:
            for item in order.items.all():
                supplier_inv = InventoryItem.objects.filter(
                    product=item.product,
                    company=order.supplier_company
                ).first()
                if not supplier_inv:
                    supplier_inv = InventoryItem.objects.filter(product=item.product).first()
                if supplier_inv:
                    supplier_inv.current_stock += item.quantity_requested
                    supplier_inv.save()

        order.save()
        return Response({
            'message': f"Order status changed to {order.get_status_display()}",
            'order': self.get_serializer(order).data
        })

    @action(detail=True, methods=['post'])
    def evaluate_order(self, request, pk=None):
        """
        Allows a Buyer to evaluate a delivered order across W1 (Timeliness), W2 (Completeness), and W3 (Price Consistency).
        Automatically recalculates and updates the supplier's evaluation scorecard.
        """
        order = self.get_object()
        if order.status != 'DELIVERED':
            return Response({'error': 'Only delivered orders can be evaluated.'}, status=status.HTTP_400_BAD_REQUEST)

        w1_timeliness = float(request.data.get('timeliness_score', 100.0))
        w2_completeness = float(request.data.get('completeness_score', 100.0))
        w3_price = float(request.data.get('price_consistency_score', 100.0))
        feedback = request.data.get('feedback', '')

        order.timeliness_score = w1_timeliness
        order.completeness_score = w2_completeness
        order.price_consistency_score = w3_price
        order.is_evaluated = True
        order.evaluation_feedback = feedback
        order.evaluated_at = timezone.now()
        order.save()

        # Recalculate Supplier Evaluation
        from apps.scoring.models import SupplierEvaluation
        
        # Get all evaluated orders for this supplier
        supplier_orders = PurchaseOrder.objects.filter(supplier_company=order.supplier_company, is_evaluated=True)
        if supplier_orders.exists():
            avg_timeliness = sum(o.timeliness_score for o in supplier_orders) / supplier_orders.count()
            avg_completeness = sum(o.completeness_score for o in supplier_orders) / supplier_orders.count()
            avg_price = sum(o.price_consistency_score for o in supplier_orders) / supplier_orders.count()
        else:
            avg_timeliness = w1_timeliness
            avg_completeness = w2_completeness
            avg_price = w3_price

        eval_record, _ = SupplierEvaluation.objects.get_or_create(
            sme_company=order.buyer_company,
            supplier_company=order.supplier_company,
            defaults={'tier': 'TIER_1'}
        )
        eval_record.delivery_timeliness_score = round(avg_timeliness, 2)
        eval_record.order_completeness_score = round(avg_completeness, 2)
        eval_record.price_consistency_score = round(avg_price, 2)
        eval_record.total_orders_evaluated = supplier_orders.count()
        
        # Weighted overall score (W1: 40%, W2: 35%, W3: 25%)
        overall = (0.40 * avg_timeliness) + (0.35 * avg_completeness) + (0.25 * avg_price)
        eval_record.overall_score = round(overall, 2)
        eval_record.update_tier()
        eval_record.save()

        return Response({
            'message': f"Order evaluated! {order.supplier_company.name} updated score: {eval_record.overall_score}% ({eval_record.get_tier_display()}).",
            'order': self.get_serializer(order).data,
            'evaluation': {
                'timeliness': avg_timeliness,
                'completeness': avg_completeness,
                'price_consistency': avg_price,
                'overall_score': eval_record.overall_score,
                'tier': eval_record.get_tier_display()
            }
        })

    @action(detail=True, methods=['post'])
    def generate_invoice(self, request, pk=None):
        order = self.get_object()
        if hasattr(order, 'invoice'):
            inv = order.invoice
        else:
            inv_number = f"INV-{timezone.now().year}-{str(order.id).zfill(4)}"
            inv = Invoice.objects.create(
                invoice_number=inv_number,
                order=order,
                issue_date=timezone.now().date(),
                due_date=timezone.now().date() + timedelta(days=30),
                tax_rate=20.00
            )
        inv.update_totals()
        return Response({
            'message': 'Invoice generated successfully',
            'invoice': InvoiceSerializer(inv).data
        })

    @action(detail=False, methods=['post'])
    def quick_reorder(self, request):
        """1-click reorder from a low stock inventory alert."""
        inventory_id = request.data.get('inventory_item_id')
        try:
            inv_item = InventoryItem.objects.get(id=inventory_id)
        except InventoryItem.DoesNotExist:
            return Response({'error': 'Inventory item not found'}, status=status.HTTP_404_NOT_FOUND)

        supplier = inv_item.product.preferred_supplier
        if not supplier:
            supplier = Company.objects.filter(company_type='SUPPLIER').first()
            if not supplier:
                return Response({'error': 'No supplier available'}, status=status.HTTP_400_BAD_REQUEST)

        order_num = f"PO-{timezone.now().year}-{str(uuid.uuid4().hex[:6]).upper()}"
        order = PurchaseOrder.objects.create(
            order_number=order_num,
            order_type='PURCHASE_ORDER',
            buyer_company=inv_item.company,
            supplier_company=supplier,
            status='PENDING_SUPPLIER',
            expected_delivery_date=timezone.now().date() + timedelta(days=5),
            notes=f"Automated reorder triggered due to critical stock level ({inv_item.current_stock} <= {inv_item.critical_threshold})"
        )

        OrderItem.objects.create(
            order=order,
            product=inv_item.product,
            quantity_requested=inv_item.reorder_quantity or 50,
            agreed_unit_price=inv_item.product.unit_price
        )
        order.calculate_total()
        return Response(PurchaseOrderSerializer(order).data, status=status.HTTP_201_CREATED)


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.select_related('order', 'order__buyer_company', 'order__supplier_company').all()
    serializer_class = InvoiceSerializer

    @action(detail=True, methods=['get'])
    def pdf(self, request, pk=None):
        invoice = self.get_object()
        pdf_content = generate_invoice_pdf(invoice)
        filename = f"{invoice.invoice_number}.pdf"
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
