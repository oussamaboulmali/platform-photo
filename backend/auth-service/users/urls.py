"""
URL configuration for users app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuthViewSet, UserViewSet, PhotographerProfileViewSet, AuditLogViewSet

router = DefaultRouter()
router.register(r'', AuthViewSet, basename='auth')
router.register(r'users', UserViewSet, basename='users')
router.register(r'profiles', PhotographerProfileViewSet, basename='profiles')
router.register(r'audit', AuditLogViewSet, basename='audit')

urlpatterns = [
    path('', include(router.urls)),
]
