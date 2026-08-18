from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CompanyViewSet, 
    UserProfileViewSet, 
    register_user, 
    login_user, 
    get_current_user, 
    logout_user
)

router = DefaultRouter()
router.register(r'companies', CompanyViewSet)
router.register(r'users', UserProfileViewSet)

urlpatterns = [
    path('auth/register/', register_user, name='auth-register'),
    path('auth/login/', login_user, name='auth-login'),
    path('auth/me/', get_current_user, name='auth-me'),
    path('auth/logout/', logout_user, name='auth-logout'),
    path('', include(router.urls)),
]
