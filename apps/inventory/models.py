from django.db import models
from apps.accounts.models import Company

class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=60, unique=True, verbose_name="SKU Code")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    description = models.TextField(blank=True, null=True)
    unit = models.CharField(max_length=30, default='Units', help_text="e.g. Units, Boxes, Kg, Liters, Pallets")
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    preferred_supplier = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supplied_products',
        limit_choices_to={'company_type': 'SUPPLIER'}
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.sku})"


class InventoryItem(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='inventory_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_entries')
    current_stock = models.IntegerField(default=0)
    critical_threshold = models.IntegerField(default=20, help_text="Triggers critical stock alert if current stock <= threshold")
    reorder_quantity = models.IntegerField(default=100, help_text="Standard replenishment quantity")
    warehouse_location = models.CharField(max_length=100, default='Main Warehouse - Bay A', blank=True)
    last_restocked_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('company', 'product')
        ordering = ['product__name']

    @property
    def is_critical(self):
        return self.current_stock <= self.critical_threshold

    @property
    def stock_health_status(self):
        if self.current_stock <= self.critical_threshold:
            return 'CRITICAL'
        elif self.current_stock <= (self.critical_threshold * 1.5):
            return 'WARNING'
        return 'HEALTHY'

    @property
    def stockout_risk_percentage(self):
        if self.critical_threshold <= 0:
            return 0
        if self.current_stock <= 0:
            return 100
        if self.current_stock >= (self.critical_threshold * 2):
            return 10
        ratio = (self.critical_threshold * 2 - self.current_stock) / (self.critical_threshold * 2)
        return min(100, max(0, int(ratio * 100)))

    def __str__(self):
        return f"{self.company.name} - {self.product.name}: {self.current_stock} {self.product.unit}"
