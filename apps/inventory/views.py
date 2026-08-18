from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, F, Q
from .models import Category, Product, InventoryItem
from .serializers import CategorySerializer, ProductSerializer, InventoryItemSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('category', 'preferred_supplier').all()
    serializer_class = ProductSerializer

    def create(self, request, *args, **kwargs):
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            if request.user.profile.company.company_type == 'SME':
                return Response({'error': 'Alıcı şirketler (Buyer) malzeme ekleyemez. Yalnızca tedarikçiler (Supplier) malzeme oluşturabilir.'}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

class InventoryItemViewSet(viewsets.ModelViewSet):
    queryset = InventoryItem.objects.select_related('company', 'product', 'product__category', 'product__preferred_supplier').all()
    serializer_class = InventoryItemSerializer

    def create(self, request, *args, **kwargs):
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            if request.user.profile.company.company_type == 'SME':
                return Response({'error': 'Alıcı şirketler (Buyer) stok kaydı oluşturamaz.'}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        company_id = self.request.query_params.get('company')
        if company_id:
            queryset = queryset.filter(Q(company_id=company_id) | Q(product__preferred_supplier_id=company_id))
        return queryset

    @action(detail=False, methods=['get'])
    def critical_alerts(self, request):
        """Returns all inventory items whose stock is at or below the critical safety threshold."""
        queryset = self.queryset
        company_id = request.query_params.get('company')
        if company_id:
            queryset = queryset.filter(Q(company_id=company_id) | Q(product__preferred_supplier_id=company_id))

        critical_items = queryset.filter(current_stock__lte=F('critical_threshold'))
        serializer = self.get_serializer(critical_items, many=True)
        return Response({
            'count': critical_items.count(),
            'status': 'WARNING' if critical_items.exists() else 'ALL_CLEAR',
            'alerts': serializer.data
        })

    @action(detail=False, methods=['get'])
    def metrics(self, request):
        """Calculates global inventory health metrics."""
        total_items = self.queryset.count()
        critical_count = self.queryset.filter(current_stock__lte=F('critical_threshold')).count()
        warning_count = self.queryset.filter(
            current_stock__gt=F('critical_threshold'),
            current_stock__lte=F('critical_threshold') * 1.5
        ).count()
        healthy_count = total_items - critical_count - warning_count
        
        # Calculate total inventory valuation
        valuation = 0.0
        for item in self.queryset:
            valuation += float(item.current_stock) * float(item.product.unit_price)

        health_rate = round(((healthy_count + warning_count * 0.5) / total_items * 100), 1) if total_items > 0 else 100

        return Response({
            'total_skus': total_items,
            'critical_count': critical_count,
            'warning_count': warning_count,
            'healthy_count': healthy_count,
            'inventory_health_rate': health_rate,
            'total_valuation': round(valuation, 2)
        })

    @action(detail=True, methods=['post'])
    def adjust_stock(self, request, pk=None):
        """Quickly adjust stock level (+ or -)"""
        item = self.get_object()
        delta = request.data.get('delta', 0)
        try:
            delta = int(delta)
        except ValueError:
            return Response({'error': 'Invalid delta integer'}, status=status.HTTP_400_BAD_REQUEST)

        item.current_stock = max(0, item.current_stock + delta)
        item.save()
        serializer = self.get_serializer(item)
        return Response({
            'message': f"Stock adjusted by {delta:+d}. New stock: {item.current_stock}",
            'item': serializer.data
        })

    @action(detail=True, methods=['post', 'patch'])
    def update_threshold(self, request, pk=None):
        """Allows suppliers to set/update the safety threshold for their items."""
        item = self.get_object()
        threshold = request.data.get('critical_threshold') or request.data.get('threshold')
        try:
            threshold = int(threshold)
            if threshold < 0:
                return Response({'error': 'Threshold must be >= 0'}, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return Response({'error': 'Invalid threshold integer'}, status=status.HTTP_400_BAD_REQUEST)

        item.critical_threshold = threshold
        item.save()
        serializer = self.get_serializer(item)
        status_msg = "🚨 CRITICAL DEFICIT (Below Safety Buffer)" if item.is_critical else "🟢 SAFE BUFFER"
        return Response({
            'message': f"Safety threshold updated to {item.critical_threshold} {item.product.unit}. Status: {status_msg}",
            'item': serializer.data,
            'is_critical': item.is_critical
        })
