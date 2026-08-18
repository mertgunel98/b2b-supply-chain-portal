from django.db import models
from django.contrib.auth.models import User

class Company(models.Model):
    COMPANY_TYPE_CHOICES = (
        ('SME', 'Small/Medium Enterprise (Buyer)'),
        ('SUPPLIER', 'Supplier / Vendor'),
    )

    name = models.CharField(max_length=255)
    company_type = models.CharField(max_length=20, choices=COMPANY_TYPE_CHOICES, default='SME')
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    contact_person = models.CharField(max_length=150, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Companies"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_company_type_display()})"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='members')
    role_title = models.CharField(max_length=100, default='Procurement Specialist')
    phone = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.company.name} ({self.role_title})"
