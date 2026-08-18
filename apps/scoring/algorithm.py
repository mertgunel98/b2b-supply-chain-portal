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
        # Directly compute exact scores from buyer evaluations
        timeliness_score = sum(o.timeliness_score for o in evaluated_orders) / evaluated_orders.count()
        completeness_score = sum(o.completeness_score for o in evaluated_orders) / evaluated_orders.count()
        price_consistency_score = sum(o.price_consistency_score for o in evaluated_orders) / evaluated_orders.count()
        on_time_count = evaluated_orders.filter(timeliness_score__gte=80).count()
        delayed_count = evaluated_orders.filter(timeliness_score__lt=80).count()
    elif total_orders == 0:
        # Default baseline score for new/untested supplier
        return {
            'timeliness': 90.0,
            'completeness': 95.0,
            'price_consistency': 98.0,
            'overall_score': round(w1 * 90.0 + w2 * 95.0 + w3 * 98.0, 2),
            'total_orders': 0,
            'on_time_count': 0,
            'delayed_count': 0,
            'weights_used': {'w1': round(w1, 3), 'w2': round(w2, 3), 'w3': round(w3, 3)}
        }
    else:
        # Fallback to delivery date heuristic if no buyer review yet
        delivered_orders = orders.filter(status='DELIVERED')
        delivered_count = delivered_orders.count()
        on_time_count = 0
        delayed_count = 0

        if delivered_count > 0:
            for order in delivered_orders:
                if order.actual_delivery_date and order.actual_delivery_date <= order.expected_delivery_date:
                    on_time_count += 1
                elif not order.actual_delivery_date:
                    on_time_count += 1
                else:
                    delayed_count += 1
            timeliness_score = (on_time_count / delivered_count) * 100.0
        else:
            timeliness_score = 92.0

        order_items = OrderItem.objects.filter(order__in=orders)
        total_requested = sum(item.quantity_requested for item in order_items)
        total_received = sum(item.quantity_received if item.quantity_received > 0 else item.quantity_requested for item in order_items)
        completeness_score = min(100.0, (total_received / total_requested) * 100.0) if total_requested > 0 else 95.0

        variance_penalties = []
        for item in order_items:
            catalog_price = float(item.product.unit_price)
            agreed_price = float(item.agreed_unit_price)
            if catalog_price > 0:
                diff_percent = abs(agreed_price - catalog_price) / catalog_price * 100.0
                variance_penalties.append(min(30.0, diff_percent))
        avg_price_variance = (sum(variance_penalties) / len(variance_penalties)) if variance_penalties else 0.0
        price_consistency_score = max(50.0, 100.0 - avg_price_variance)

    # Overall calculation
    overall_score = (w1 * timeliness_score) + (w2 * completeness_score) + (w3 * price_consistency_score)

    return {
        'timeliness': round(timeliness_score, 1),
        'completeness': round(completeness_score, 1),
        'price_consistency': round(price_consistency_score, 1),
        'overall_score': round(overall_score, 1),
        'total_orders': total_orders,
        'on_time_count': on_time_count,
        'delayed_count': delayed_count,
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
