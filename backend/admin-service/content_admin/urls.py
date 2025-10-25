from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BlocViewSet, AdSlotViewSet

router = DefaultRouter()
router.register(r'blocs', BlocViewSet, basename='blocs')
router.register(r'ads', AdSlotViewSet, basename='ads')

urlpatterns = [path('', include(router.urls))]
