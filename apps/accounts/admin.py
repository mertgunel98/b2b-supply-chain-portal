from django.contrib import admin
from .models import Company, UserProfile

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'company_type', 'contact_person', 'email', 'phone', 'created_at')
    list_filter = ('company_type',)
    search_fields = ('name', 'contact_person', 'email', 'tax_id')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'role_title', 'phone')
    list_filter = ('company__company_type',)
