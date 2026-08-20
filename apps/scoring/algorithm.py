from django.db.models import Avg, Sum, F, ExpressionWrapper, DecimalField
from .models import ScoringConfiguration, SupplierEvaluation
from apps.orders.models import PurchaseOrder, OrderItem
from apps.accounts.models import Company

def calculate_supplier_score(sme_company, supplier_company, custom_weights=None):
    """
    Computes the weighted multi-criteria supplier performance score:
    Performance Score = (W1 * Delivery Timeliness) + (W2 * Order Completeness) + (W3 * Price Consistency)
    """
    # 1. Obtain Weights
    if custom_weights:
        w1 = float(custom_weights.get('w1', 0.40))
        w2 = float(custom_weights.get('w2', 0.35))
        w3 = float(custom_weights.get('w3', 0.25))
    else:
        config, _ = ScoringConfiguration.objects.get_or_create(
            sme_company=sme_company,
            defaults={'w1_timeliness': 0.40, 'w2_completeness': 0.35, 'w3_price_consistency': 0.25}
        )
        w1 = config.w1_timeliness
        w2 = config.w2_completeness
        w3 = config.w3_price_consistency

    # Normalize weights so sum = 1.0
    weight_sum = w1 + w2 + w3
    if weight_sum > 0:
        w1, w2, w3 = w1 / weight_sum, w2 / weight_sum, w3 / weight_sum
    else:
        w1, w2, w3 = 0.40, 0.35, 0.25

    # 2. Fetch completed/relevant orders between this SME and Supplier
    orders = PurchaseOrder.objects.filter(
        buyer_company=sme_company,
        supplier_company=supplier_company,
        status__in=['DELIVERED', 'IN_TRANSIT', 'CONFIRMED']
    )

    total_orders = orders.count()
    evaluated_orders = orders.filter(is_evaluated=True)

    if evaluated_orders.exists():
        # Directly compute exact weighted average from buyer evaluations
        timeliness_score = sum(o.timeliness_score for o in evaluated_orders) / evaluated_orders.count()
        completeness_score = sum(o.completeness_score for o in evaluated_orders) / evaluated_orders.count()
        price_consistency_score = sum(o.price_consistency_score for o in evaluated_orders) / evaluated_orders.count()
        on_time_count = evaluated_orders.filter(timeliness_score__gte=80).count()
        delayed_count = evaluated_orders.filter(timeliness_score__lt=80).count()
        overall_score = (w1 * timeliness_score) + (w2 * completeness_score) + (w3 * price_consistency_score)
        return {
            'timeliness': round(timeliness_score, 1),
            'completeness': round(completeness_score, 1),
            'price_consistency': round(price_consistency_score, 1),
            'overall_score': round(overall_score, 1),
            'has_evaluations': True,
            'total_orders': total_orders,
            'evaluated_count': evaluated_orders.count(),
            'on_time_count': on_time_count,
            'delayed_count': delayed_count,
            'weights_used': {'w1': round(w1, 3), 'w2': round(w2, 3), 'w3': round(w3, 3)}
        }
    else:
        # New or unreviewed supplier: No evaluations yet
        return {
            'timeliness': 0.0,
            'completeness': 0.0,
            'price_consistency': 0.0,
            'overall_score': 0.0,
            'has_evaluations': False,
            'total_orders': total_orders,
            'evaluated_count': 0,
            'on_time_count': 0,
            'delayed_count': 0,
            'weights_used': {'w1': round(w1, 3), 'w2': round(w2, 3), 'w3': round(w3, 3)}
        }


def refresh_all_supplier_evaluations(sme_company=None):
    """Refreshes and persists evaluation score records in the database."""
    smes = [sme_company] if sme_company else Company.objects.filter(company_type='SME')
    suppliers = Company.objects.filter(company_type='SUPPLIER')

    results = []
    for sme in smes:
        for supplier in suppliers:
            score_data = calculate_supplier_score(sme, supplier)
            evaluation, _ = SupplierEvaluation.objects.get_or_create(
                sme_company=sme,
                supplier_company=supplier
            )
            evaluation.delivery_timeliness_score = score_data['timeliness']
            evaluation.order_completeness_score = score_data['completeness']
            evaluation.price_consistency_score = score_data['price_consistency']
            evaluation.overall_score = score_data['overall_score']
            evaluation.total_orders_evaluated = score_data['total_orders']
            evaluation.on_time_orders_count = score_data['on_time_count']
            evaluation.delayed_orders_count = score_data['delayed_count']
            evaluation.update_tier()
            evaluation.save()
            results.append(evaluation)
    return results
