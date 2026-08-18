from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import PortalHomeView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', PortalHomeView.as_view(), name='portal-home'),

    # REST APIs
    path('api/accounts/', include('apps.accounts.urls')),
    path('api/inventory/', include('apps.inventory.urls')),
    path('api/orders/', include('apps.orders.urls')),
    path('api/scoring/', include('apps.scoring.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
