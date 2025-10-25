"""
URL configuration for images app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, TopicViewSet, PlaceViewSet,
    ImageViewSet, ReviewViewSet, UploadTaskViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='categories')
router.register(r'topics', TopicViewSet, basename='topics')
router.register(r'places', PlaceViewSet, basename='places')
router.register(r'images', ImageViewSet, basename='images')
router.register(r'reviews', ReviewViewSet, basename='reviews')
router.register(r'uploads', UploadTaskViewSet, basename='uploads')

urlpatterns = [
    path('', include(router.urls)),
]
