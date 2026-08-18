from django.contrib import admin
from .models import Category, Product, InventoryItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'unit', 'unit_price', 'preferred_supplier')
    list_filter = ('category', 'preferred_supplier')
    search_fields = ('name', 'sku')

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'company', 'current_stock', 'critical_threshold', 'is_critical', 'warehouse_location')
    list_filter = ('company', 'warehouse_location')
    search_fields = ('product__name', 'product__sku')
