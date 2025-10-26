"""
Admin configuration for images app
"""
from django.contrib import admin
from .models import (
    Category, Topic, Place, Image, ImageDerivative,
    ImageMetadata, Review, UploadTask
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'slug', 'order', 'is_active', 'created_at']
    list_filter = ['is_active', 'parent']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'slug', 'is_active', 'created_at']
    list_filter = ['type', 'is_active']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'slug', 'is_active', 'created_at']
    list_filter = ['type', 'is_active']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


class ImageDerivativeInline(admin.TabularInline):
    model = ImageDerivative
    extra = 0
    readonly_fields = ['kind', 'file_path', 'width', 'height', 'filesize', 'is_watermarked']


class ImageMetadataInline(admin.TabularInline):
    model = ImageMetadata
    extra = 1


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ['filename', 'uploader_email', 'type', 'status', 'category', 'created_at', 'published_at']
    list_filter = ['status', 'type', 'orientation', 'created_at']
    search_fields = ['filename', 'uploader_email', 'md5']
    inlines = [ImageDerivativeInline, ImageMetadataInline]
    readonly_fields = ['md5', 'width', 'height', 'filesize', 'mime_type', 'orientation']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['image', 'reviewer_email', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['image__filename', 'reviewer_email']


@admin.register(UploadTask)
class UploadTaskAdmin(admin.ModelAdmin):
    list_display = ['original_filename', 'uploader_id', 'status', 'created_at', 'finished_at']
    list_filter = ['status', 'created_at']
    search_fields = ['original_filename']
    readonly_fields = ['uploader_id', 'original_filename', 'file_path', 'status', 'error_message']
