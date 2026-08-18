from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ScoringConfiguration, SupplierEvaluation
from .serializers import ScoringConfigurationSerializer, SupplierEvaluationSerializer
from .algorithm import calculate_supplier_score, refresh_all_supplier_evaluations
from apps.accounts.models import Company

class ScoringConfigurationViewSet(viewsets.ModelViewSet):
    queryset = ScoringConfiguration.objects.all()
    serializer_class = ScoringConfigurationSerializer


class SupplierEvaluationViewSet(viewsets.ModelViewSet):
    queryset = SupplierEvaluation.objects.select_related('sme_company', 'supplier_company').all()
    serializer_class = SupplierEvaluationSerializer

    @action(detail=False, methods=['post'])
    def simulate(self, request):
        """Simulates supplier scores with dynamic weight adjustments from frontend sliders."""
        w1 = float(request.data.get('w1', 0.40))
        w2 = float(request.data.get('w2', 0.35))
        w3 = float(request.data.get('w3', 0.25))

        sme = Company.objects.filter(company_type='SME').first()
        suppliers = Company.objects.filter(company_type='SUPPLIER')

        if not sme:
            return Response({'error': 'No SME company found in system.'}, status=status.HTTP_400_BAD_REQUEST)

        results = []
        for supplier in suppliers:
            score_data = calculate_supplier_score(sme, supplier, {'w1': w1, 'w2': w2, 'w3': w3})
            
            # Determine simulated tier
            overall = score_data['overall_score']
            if overall >= 90:
                tier = 'Tier 1 - Gold (Preferred)'
            elif overall >= 75:
                tier = 'Tier 2 - Silver (Reliable)'
            elif overall >= 60:
                tier = 'Tier 3 - Bronze (Needs Improvement)'
            else:
                tier = 'Tier 4 - Restricted (High Risk)'

            results.append({
                'supplier_id': supplier.id,
                'supplier_name': supplier.name,
                'tax_id': supplier.tax_id,
                'contact_person': supplier.contact_person,
                'email': supplier.email,
                'phone': supplier.phone,
                'timeliness_score': score_data['timeliness'],
                'completeness_score': score_data['completeness'],
                'price_consistency_score': score_data['price_consistency'],
                'overall_score': score_data['overall_score'],
                'tier': tier,
                'total_orders': score_data['total_orders'],
                'on_time_count': score_data['on_time_count'],
                'delayed_count': score_data['delayed_count']
            })

        results.sort(key=lambda x: x['overall_score'], reverse=True)
        return Response({
            'weights_applied': {'w1': w1, 'w2': w2, 'w3': w3},
            'formula': 'Score = (W1 * Timeliness) + (W2 * Completeness) + (W3 * Price Consistency)',
            'leaderboard': results
        })

    @action(detail=False, methods=['post'])
    def refresh_database(self, request):
        """Refreshes and persists all supplier scores into DB records."""
        evals = refresh_all_supplier_evaluations()
        serializer = self.get_serializer(evals, many=True)
        return Response({
            'message': f'Successfully updated {len(evals)} supplier evaluation records.',
            'evaluations': serializer.data
        })
