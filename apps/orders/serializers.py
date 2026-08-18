from rest_framework import serializers
from .models import PurchaseOrder, OrderItem, Invoice
from apps.accounts.serializers import CompanySerializer
from apps.inventory.serializers import ProductSerializer
from apps.inventory.models import Product

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product', write_only=True
    )

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_id', 'quantity_requested', 'quantity_received', 'agreed_unit_price', 'line_total']


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = '__all__'


class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, required=False)
    buyer_company_details = CompanySerializer(source='buyer_company', read_only=True)
    supplier_company_details = CompanySerializer(source='supplier_company', read_only=True)
    invoice = InvoiceSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    order_type_display = serializers.CharField(source='get_order_type_display', read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'order_number', 'order_type', 'order_type_display',
            'buyer_company', 'buyer_company_details',
            'supplier_company', 'supplier_company_details',
            'status', 'status_display', 'total_amount',
            'expected_delivery_date', 'actual_delivery_date', 'notes',
            'is_evaluated', 'timeliness_score', 'completeness_score',
            'price_consistency_score', 'evaluation_feedback', 'evaluated_at',
            'created_at', 'updated_at', 'items', 'invoice'
        ]

    def validate(self, attrs):
        request = self.context.get('request')
        items_data = attrs.get('items')
        if not items_data and request:
            items_data = request.data.get('items', [])
        
        supplier = attrs.get('supplier_company')
        from apps.inventory.models import InventoryItem, Product
        
        for item_data in items_data:
            if isinstance(item_data, dict):
                product_id = item_data.get('product_id') or item_data.get('product')
                if hasattr(product_id, 'id'):
                    product_id = product_id.id
                qty = int(item_data.get('quantity_requested', 1))
                try:
                    product = Product.objects.get(id=product_id)
                except Product.DoesNotExist:
                    raise serializers.ValidationError("Geçersiz ürün seçildi.")
                
                supplier_inv = InventoryItem.objects.filter(
                    product=product,
                    company=supplier
                ).first()
                if not supplier_inv:
                    supplier_inv = InventoryItem.objects.filter(product=product).first()
                
                available = supplier_inv.current_stock if supplier_inv else 0
                if qty > available:
                    raise serializers.ValidationError(
                        f"Yetersiz Stok! '{product.name}' için talep edilen miktar ({qty}), tedarikçinin mevcut stok miktarını ({available}) aşıyor. En fazla {available} adet sipariş edebilirsiniz."
                    )
                if qty <= 0:
                    raise serializers.ValidationError("Sipariş miktarı en az 1 olmalıdır.")
        return attrs

    def create(self, validated_data):
        items_data = validated_data.pop('items', None)
        if not items_data and self.context.get('request'):
            items_data = self.context.get('request').data.get('items', [])
        elif items_data is None:
            items_data = []

        order = PurchaseOrder.objects.create(**validated_data)
        
        from apps.inventory.models import InventoryItem
        for item_data in items_data:
            if isinstance(item_data, dict):
                product_id = item_data.get('product_id') or item_data.get('product')
                if hasattr(product_id, 'id'):
                    product_id = product_id.id
                qty = int(item_data.get('quantity_requested', 1))
                product = Product.objects.get(id=product_id)
                unit_price = float(item_data.get('agreed_unit_price', product.unit_price))
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity_requested=qty,
                    agreed_unit_price=unit_price
                )

                # DEDUCT STOCK FROM SUPPLIER INVENTORY
                supplier_inv = InventoryItem.objects.filter(
                    product=product,
                    company=order.supplier_company
                ).first()
                if not supplier_inv:
                    supplier_inv = InventoryItem.objects.filter(product=product).first()
                if supplier_inv:
                    supplier_inv.current_stock = max(0, supplier_inv.current_stock - qty)
                    supplier_inv.save()

        order.calculate_total()
        return order
