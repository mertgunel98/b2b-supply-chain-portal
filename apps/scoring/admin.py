from django.contrib import admin
from .models import ScoringConfiguration, SupplierEvaluation

@admin.register(ScoringConfiguration)
class ScoringConfigurationAdmin(admin.ModelAdmin):
    list_display = ('sme_company', 'w1_timeliness', 'w2_completeness', 'w3_price_consistency', 'updated_at')

@admin.register(SupplierEvaluation)
class SupplierEvaluationAdmin(admin.ModelAdmin):
    list_display = ('supplier_company', 'sme_company', 'overall_score', 'tier', 'delivery_timeliness_score', 'order_completeness_score', 'last_evaluated_at')
    list_filter = ('tier', 'sme_company')
    search_fields = ('supplier_company__name',)
