from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.accounts.models import Company

class ScoringConfiguration(models.Model):
    sme_company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='scoring_config')
    w1_timeliness = models.FloatField(default=0.40, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)], verbose_name="Weight 1: Delivery Timeliness")
    w2_completeness = models.FloatField(default=0.35, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)], verbose_name="Weight 2: Order Completeness")
    w3_price_consistency = models.FloatField(default=0.25, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)], verbose_name="Weight 3: Price Consistency")
    updated_at = models.DateTimeField(auto_now=True)

    def normalize_weights(self):
        total = self.w1_timeliness + self.w2_completeness + self.w3_price_consistency
        if total > 0 and abs(total - 1.0) > 0.001:
            self.w1_timeliness = round(self.w1_timeliness / total, 3)
            self.w2_completeness = round(self.w2_completeness / total, 3)
            self.w3_price_consistency = round(1.0 - self.w1_timeliness - self.w2_completeness, 3)

    def __str__(self):
        return f"Scoring Config ({self.sme_company.name}) - W1:{self.w1_timeliness} W2:{self.w2_completeness} W3:{self.w3_price_consistency}"


class SupplierEvaluation(models.Model):
    TIER_CHOICES = (
        ('TIER_1', 'Tier 1 - Gold (Preferred)'),
        ('TIER_2', 'Tier 2 - Silver (Reliable)'),
        ('TIER_3', 'Tier 3 - Bronze (Needs Improvement)'),
        ('TIER_4', 'Tier 4 - Restricted (High Risk)'),
    )

    sme_company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='evaluations_given')
    supplier_company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='evaluations_received')
    
    delivery_timeliness_score = models.FloatField(default=100.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    order_completeness_score = models.FloatField(default=100.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    price_consistency_score = models.FloatField(default=100.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    overall_score = models.FloatField(default=100.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='TIER_1')
    
    total_orders_evaluated = models.IntegerField(default=0)
    on_time_orders_count = models.IntegerField(default=0)
    delayed_orders_count = models.IntegerField(default=0)
    
    last_evaluated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('sme_company', 'supplier_company')
        ordering = ['-overall_score']

    def update_tier(self):
        if self.overall_score >= 90:
            self.tier = 'TIER_1'
        elif self.overall_score >= 75:
            self.tier = 'TIER_2'
        elif self.overall_score >= 60:
            self.tier = 'TIER_3'
        else:
            self.tier = 'TIER_4'

    def __str__(self):
        return f"{self.supplier_company.name}: {self.overall_score:.1f}% ({self.get_tier_display()})"
