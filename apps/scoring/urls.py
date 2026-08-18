from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ScoringConfigurationViewSet, SupplierEvaluationViewSet

router = DefaultRouter()
router.register(r'configurations', ScoringConfigurationViewSet)
router.register(r'evaluations', SupplierEvaluationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
