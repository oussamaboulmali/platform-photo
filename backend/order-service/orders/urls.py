"""
URL configuration for orders app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserWalletViewSet, TopUpRequestViewSet, SubscriptionPlanViewSet,
    UserSubscriptionViewSet, OrderViewSet, PaymentLogViewSet
)

router = DefaultRouter()
router.register(r'wallets', UserWalletViewSet, basename='wallets')
router.register(r'topups', TopUpRequestViewSet, basename='topups')
router.register(r'plans', SubscriptionPlanViewSet, basename='plans')
router.register(r'subscriptions', UserSubscriptionViewSet, basename='subscriptions')
router.register(r'orders', OrderViewSet, basename='orders')
router.register(r'payment-logs', PaymentLogViewSet, basename='payment-logs')

urlpatterns = [
    path('', include(router.urls)),
]
