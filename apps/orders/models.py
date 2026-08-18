from django.db import models
from django.utils import timezone
from apps.accounts.models import Company
from apps.inventory.models import Product

from datetime import timedelta

def get_default_delivery_date():
    return (timezone.now() + timedelta(days=5)).date()

class PurchaseOrder(models.Model):
    ORDER_TYPE_CHOICES = (
        ('PURCHASE_ORDER', 'Purchase Order (PO)'),
        ('RFQ', 'Request for Quotation (RFQ)'),
    )

    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('PENDING_SUPPLIER', 'Pending Supplier Approval'),
        ('CONFIRMED', 'Confirmed by Supplier'),
        ('IN_TRANSIT', 'In Transit / Shipped'),
        ('DELIVERED', 'Delivered & Received'),
        ('REJECTED_BY_SUPPLIER', 'Declined by Supplier'),
        ('REJECTED_BY_BUYER', 'Rejected by Buyer'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    )

    order_number = models.CharField(max_length=64, unique=True)
    order_type = models.CharField(max_length=30, choices=ORDER_TYPE_CHOICES, default='PURCHASE_ORDER')
    buyer_company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='purchase_orders_placed')
    supplier_company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='sales_orders_received')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING_SUPPLIER')
    
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    expected_delivery_date = models.DateField(default=get_default_delivery_date)
    actual_delivery_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    # Buyer Evaluation Metrics (W1, W2, W3)
    is_evaluated = models.BooleanField(default=False)
    timeliness_score = models.FloatField(default=100.0, verbose_name="Delivery Timeliness (W1)")
    completeness_score = models.FloatField(default=100.0, verbose_name="Order Completeness (W2)")
    price_consistency_score = models.FloatField(default=100.0, verbose_name="Price Consistency (W3)")
    evaluation_feedback = models.TextField(blank=True, null=True)
    evaluated_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def calculate_total(self):
        total = sum(item.line_total for item in self.items.all())
        self.total_amount = total
        self.save(update_fields=['total_amount'])
        return total

    def __str__(self):
        return f"{self.order_number} ({self.get_status_display()}) - {self.supplier_company.name}"


class OrderItem(models.Model):
    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_items')
    quantity_requested = models.IntegerField(default=1)
    quantity_received = models.IntegerField(default=0)
    agreed_unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        self.line_total = self.quantity_requested * self.agreed_unit_price
        super().save(*args, **kwargs)
        if self.order_id:
            self.order.calculate_total()

    def __str__(self):
        return f"{self.product.name} x {self.quantity_requested} ({self.order.order_number})"


from decimal import Decimal

class Invoice(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ('UNPAID', 'Unpaid'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
    )

    invoice_number = models.CharField(max_length=64, unique=True)
    order = models.OneToOneField(PurchaseOrder, on_delete=models.CASCADE, related_name='invoice')
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=20.00, help_text="e.g. 20.00 for 20% VAT")
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    grand_total = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='UNPAID')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-issue_date']

    def update_totals(self):
        sub = Decimal(str(self.order.total_amount))
        rate = Decimal(str(self.tax_rate))
        self.subtotal = sub
        self.tax_amount = round(sub * (rate / Decimal('100')), 2)
        self.grand_total = sub + self.tax_amount
        self.save()

    def __str__(self):
        return f"Invoice {self.invoice_number} for Order {self.order.order_number} (${self.grand_total})"
