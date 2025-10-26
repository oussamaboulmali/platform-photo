"""
Serializers for Image service
"""
from rest_framework import serializers
from .models import (
    Category, Topic, Place, Image, ImageDerivative, 
    ImageMetadata, Review, UploadTask
)


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category"""
    subcategories = serializers.SerializerMethodField()
    full_path = serializers.CharField(source='get_full_path', read_only=True)

    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_subcategories(self, obj):
        if obj.subcategories.exists():
            return CategorySerializer(obj.subcategories.filter(is_active=True), many=True).data
        return []


class TopicSerializer(serializers.ModelSerializer):
    """Serializer for Topic"""
    class Meta:
        model = Topic
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class PlaceSerializer(serializers.ModelSerializer):
    """Serializer for Place"""
    class Meta:
        model = Place
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class ImageDerivativeSerializer(serializers.ModelSerializer):
    """Serializer for ImageDerivative"""
    url = serializers.SerializerMethodField()

    class Meta:
        model = ImageDerivative
        fields = ['id', 'kind', 'width', 'height', 'filesize', 'is_watermarked', 'url', 'created_at']

    def get_url(self, obj):
        # Return relative URL (to be handled by gateway/frontend)
        return f"/media/{obj.file_path}"


class ImageMetadataSerializer(serializers.ModelSerializer):
    """Serializer for ImageMetadata"""
    class Meta:
        model = ImageMetadata
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ImageSerializer(serializers.ModelSerializer):
    """Serializer for Image"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    topics_list = TopicSerializer(source='topics', many=True, read_only=True)
    places_list = PlaceSerializer(source='places', many=True, read_only=True)
    derivatives_list = ImageDerivativeSerializer(source='derivatives', many=True, read_only=True)
    metadata_list = ImageMetadataSerializer(source='metadata', many=True, read_only=True)

    class Meta:
        model = Image
        fields = [
            'id', 'uploader_id', 'uploader_email', 'filename', 'type', 'status',
            'width', 'height', 'orientation', 'filesize', 'mime_type',
            'category', 'category_name', 'topics_list', 'places_list',
            'derivatives_list', 'metadata_list',
            'view_count', 'download_count', 'purchase_count',
            'created_at', 'updated_at', 'submitted_at', 'published_at'
        ]
        read_only_fields = [
            'id', 'md5', 'width', 'height', 'orientation', 'filesize', 'mime_type',
            'view_count', 'download_count', 'purchase_count',
            'created_at', 'updated_at', 'submitted_at', 'published_at'
        ]


class ImageListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for image lists"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    thumbnail_url = serializers.SerializerMethodField()
    preview_url = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = [
            'id', 'filename', 'type', 'status', 'width', 'height', 'orientation',
            'category_name', 'thumbnail_url', 'preview_url',
            'view_count', 'purchase_count', 'created_at', 'published_at'
        ]

    def get_thumbnail_url(self, obj):
        thumbnail = obj.derivatives.filter(kind='thumbnail').first()
        return f"/media/{thumbnail.file_path}" if thumbnail else None

    def get_preview_url(self, obj):
        preview = obj.derivatives.filter(kind='preview').first()
        return f"/media/{preview.file_path}" if preview else None


class ImageUploadSerializer(serializers.Serializer):
    """Serializer for image upload"""
    file = serializers.FileField()
    type = serializers.ChoiceField(choices=['photo', 'infographie'], default='photo')
    title = serializers.CharField(max_length=500, required=False)
    caption = serializers.CharField(required=False, allow_blank=True)
    category_id = serializers.IntegerField(required=False)
    topic_ids = serializers.ListField(child=serializers.IntegerField(), required=False)
    place_ids = serializers.ListField(child=serializers.IntegerField(), required=False)
    keywords = serializers.ListField(child=serializers.CharField(), required=False)


class ImageUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating image metadata"""
    topic_ids = serializers.ListField(child=serializers.IntegerField(), required=False, write_only=True)
    place_ids = serializers.ListField(child=serializers.IntegerField(), required=False, write_only=True)

    class Meta:
        model = Image
        fields = ['category', 'topic_ids', 'place_ids', 'status']

    def update(self, instance, validated_data):
        topic_ids = validated_data.pop('topic_ids', None)
        place_ids = validated_data.pop('place_ids', None)

        # Update simple fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update many-to-many relationships
        if topic_ids is not None:
            instance.topics.set(Topic.objects.filter(id__in=topic_ids))
        if place_ids is not None:
            instance.places.set(Place.objects.filter(id__in=place_ids))

        return instance


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for Review"""
    image_filename = serializers.CharField(source='image.filename', read_only=True)

    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ReviewActionSerializer(serializers.Serializer):
    """Serializer for review actions (approve/reject)"""
    comment = serializers.CharField(required=False, allow_blank=True)
    metadata_changes = serializers.JSONField(required=False)


class UploadTaskSerializer(serializers.ModelSerializer):
    """Serializer for UploadTask"""
    image_data = ImageListSerializer(source='image', read_only=True)

    class Meta:
        model = UploadTask
        fields = '__all__'
        read_only_fields = ['id', 'status', 'error_message', 'created_at', 'finished_at']


class SearchSerializer(serializers.Serializer):
    """Serializer for search parameters"""
    q = serializers.CharField(required=False, allow_blank=True)
    category = serializers.IntegerField(required=False)
    topic = serializers.IntegerField(required=False)
    place = serializers.IntegerField(required=False)
    type = serializers.ChoiceField(choices=['photo', 'infographie'], required=False)
    orientation = serializers.ChoiceField(
        choices=['landscape', 'portrait', 'square'],
        required=False
    )
    status = serializers.ChoiceField(
        choices=['draft', 'submitted', 'in_review', 'rejected', 'published', 'archived'],
        required=False
    )
    min_width = serializers.IntegerField(required=False)
    max_width = serializers.IntegerField(required=False)
    date_from = serializers.DateTimeField(required=False)
    date_to = serializers.DateTimeField(required=False)
