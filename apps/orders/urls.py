from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PurchaseOrderViewSet, InvoiceViewSet

router = DefaultRouter()
router.register(r'purchase-orders', PurchaseOrderViewSet)
router.register(r'invoices', InvoiceViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
