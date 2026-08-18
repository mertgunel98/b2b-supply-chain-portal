from rest_framework import serializers
from .models import ScoringConfiguration, SupplierEvaluation
from apps.accounts.serializers import CompanySerializer

class ScoringConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScoringConfiguration
        fields = '__all__'


class SupplierEvaluationSerializer(serializers.ModelSerializer):
    supplier_company = CompanySerializer(read_only=True)
    sme_company_name = serializers.CharField(source='sme_company.name', read_only=True)
    tier_display = serializers.CharField(source='get_tier_display', read_only=True)

    class Meta:
        model = SupplierEvaluation
        fields = [
            'id', 'sme_company', 'sme_company_name',
            'supplier_company', 'delivery_timeliness_score',
            'order_completeness_score', 'price_consistency_score',
            'overall_score', 'tier', 'tier_display',
            'total_orders_evaluated', 'on_time_orders_count', 'delayed_orders_count',
            'last_evaluated_at'
        ]
