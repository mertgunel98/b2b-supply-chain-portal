from django.contrib import admin
from .models import PurchaseOrder, OrderItem, Invoice

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'order_type', 'buyer_company', 'supplier_company', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'order_type', 'buyer_company', 'supplier_company')
    search_fields = ('order_number', 'notes')
    inlines = [OrderItemInline]

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'order', 'issue_date', 'due_date', 'grand_total', 'payment_status')
    list_filter = ('payment_status', 'issue_date')
    search_fields = ('invoice_number', 'order__order_number')
