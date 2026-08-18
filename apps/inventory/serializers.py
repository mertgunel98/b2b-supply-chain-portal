from rest_framework import serializers
from .models import Category, Product, InventoryItem
from apps.accounts.serializers import CompanySerializer

class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(source='products.count', read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'product_count']


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    preferred_supplier_name = serializers.CharField(source='preferred_supplier.name', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'category', 'category_name', 
            'description', 'unit', 'unit_price', 
            'preferred_supplier', 'preferred_supplier_name', 'created_at'
        ]


class InventoryItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product', write_only=True
    )
    company_name = serializers.CharField(source='company.name', read_only=True)
    is_critical = serializers.BooleanField(read_only=True)
    stock_health_status = serializers.CharField(read_only=True)
    stockout_risk_percentage = serializers.IntegerField(read_only=True)

    class Meta:
        model = InventoryItem
        fields = [
            'id', 'company', 'company_name', 'product', 'product_id',
            'current_stock', 'critical_threshold', 'reorder_quantity',
            'warehouse_location', 'last_restocked_at', 'is_critical',
            'stock_health_status', 'stockout_risk_percentage'
        ]
