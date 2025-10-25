"""
Views for Image service
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from django.contrib.postgres.search import SearchQuery, SearchRank
import os
import uuid
from .models import (
    Category, Topic, Place, Image, ImageDerivative,
    ImageMetadata, Review, UploadTask
)
from .serializers import (
    CategorySerializer, TopicSerializer, PlaceSerializer,
    ImageSerializer, ImageListSerializer, ImageUploadSerializer,
    ImageUpdateSerializer, ImageMetadataSerializer,
    ReviewSerializer, ReviewActionSerializer, UploadTaskSerializer,
    SearchSerializer, ImageDerivativeSerializer
)
from .tasks import process_upload, create_derivatives, reindex_search


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for Category management"""
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = self.queryset
        # Only return root categories for list view
        if self.action == 'list':
            queryset = queryset.filter(parent__isnull=True)
        return queryset


class TopicViewSet(viewsets.ModelViewSet):
    """ViewSet for Topic management"""
    queryset = Topic.objects.filter(is_active=True)
    serializer_class = TopicSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class PlaceViewSet(viewsets.ModelViewSet):
    """ViewSet for Place management"""
    queryset = Place.objects.filter(is_active=True)
    serializer_class = PlaceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ImageViewSet(viewsets.ModelViewSet):
    """ViewSet for Image management"""
    queryset = Image.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return ImageListSerializer
        return ImageSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = self.queryset

        # Filter based on user role (role passed via JWT or header)
        user_role = self.request.META.get('HTTP_X_USER_ROLE', 'customer')
        user_id = self.request.META.get('HTTP_X_USER_ID', user.id)

        if user_role == 'admin':
            # Admins see everything
            pass
        elif user_role in ['photographer', 'infographiste']:
            # Users see only their own images
            queryset = queryset.filter(uploader_id=user_id)
        elif user_role == 'validator':
            # Validators see submitted and in_review images
            queryset = queryset.filter(status__in=['submitted', 'in_review', 'published'])
        else:
            # Public users see only published images
            queryset = queryset.filter(status='published')

        # Apply filters
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        type_filter = self.request.query_params.get('type')
        if type_filter:
            queryset = queryset.filter(type=type_filter)

        category_filter = self.request.query_params.get('category')
        if category_filter:
            queryset = queryset.filter(category_id=category_filter)

        return queryset.order_by('-created_at')

    @action(detail=False, methods=['post'])
    def upload(self, request):
        """Upload a new image"""
        serializer = ImageUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = serializer.validated_data['file']
        image_type = serializer.validated_data.get('type', 'photo')
        
        # Get user info from JWT/headers
        user_id = request.META.get('HTTP_X_USER_ID')
        user_email = request.META.get('HTTP_X_USER_EMAIL')
        user_role = request.META.get('HTTP_X_USER_ROLE')

        if not user_id or not user_email:
            return Response(
                {'error': 'User authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Check permissions
        if image_type == 'infographie' and user_role != 'infographiste':
            return Response(
                {'error': 'Only infographistes can upload infographie type'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Generate storage path
        now = timezone.now()
        filename = f"{uuid.uuid4()}_{uploaded_file.name}"
        rel_path = os.path.join(
            str(now.year),
            f"{now.month:02d}",
            f"user_{user_id}",
            filename
        )
        full_path = os.path.join(settings.STORAGE_ROOT, rel_path)

        # Ensure directory exists
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # Save file
        with open(full_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        # Create upload task
        upload_task = UploadTask.objects.create(
            uploader_id=user_id,
            original_filename=uploaded_file.name,
            file_path=rel_path,
            status='pending'
        )

        # Trigger async processing
        process_upload.delay(upload_task.id)

        return Response({
            'message': 'Upload initiated',
            'upload_task_id': upload_task.id
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit image for review"""
        image = self.get_object()
        user_id = request.META.get('HTTP_X_USER_ID')

        if str(image.uploader_id) != str(user_id):
            return Response(
                {'error': 'You can only submit your own images'},
                status=status.HTTP_403_FORBIDDEN
            )

        if image.status not in ['draft']:
            return Response(
                {'error': 'Only draft images can be submitted'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if metadata exists
        if not image.metadata.exists():
            return Response(
                {'error': 'Please add metadata before submitting'},
                status=status.HTTP_400_BAD_REQUEST
            )

        image.status = 'submitted'
        image.submitted_at = timezone.now()
        image.save()

        return Response({
            'message': 'Image submitted for review',
            'image': ImageSerializer(image).data
        })

    @action(detail=True, methods=['put'])
    def update_metadata(self, request, pk=None):
        """Update image metadata"""
        image = self.get_object()
        language = request.data.get('language', 'en')

        metadata, created = ImageMetadata.objects.update_or_create(
            image=image,
            language=language,
            defaults={
                'title': request.data.get('title', ''),
                'caption': request.data.get('caption', ''),
                'keywords': request.data.get('keywords', []),
                'alt_text': request.data.get('alt_text', ''),
                'photographer_name': request.data.get('photographer_name', ''),
                'copyright_info': request.data.get('copyright_info', ''),
            }
        )

        # Trigger search reindex
        reindex_search.delay(image.id)

        return Response({
            'message': 'Metadata updated',
            'metadata': ImageMetadataSerializer(metadata).data
        })

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search images with full-text search"""
        search_serializer = SearchSerializer(data=request.query_params)
        if not search_serializer.is_valid():
            return Response(search_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.get_queryset()
        data = search_serializer.validated_data

        # Text search
        q = data.get('q')
        if q:
            search_query = SearchQuery(q)
            queryset = queryset.filter(search_vector=search_query)
            queryset = queryset.annotate(rank=SearchRank('search_vector', search_query))
            queryset = queryset.order_by('-rank')

        # Filters
        if 'category' in data:
            queryset = queryset.filter(category_id=data['category'])
        if 'topic' in data:
            queryset = queryset.filter(topics__id=data['topic'])
        if 'place' in data:
            queryset = queryset.filter(places__id=data['place'])
        if 'type' in data:
            queryset = queryset.filter(type=data['type'])
        if 'orientation' in data:
            queryset = queryset.filter(orientation=data['orientation'])
        if 'status' in data:
            queryset = queryset.filter(status=data['status'])
        if 'min_width' in data:
            queryset = queryset.filter(width__gte=data['min_width'])
        if 'max_width' in data:
            queryset = queryset.filter(width__lte=data['max_width'])
        if 'date_from' in data:
            queryset = queryset.filter(created_at__gte=data['date_from'])
        if 'date_to' in data:
            queryset = queryset.filter(created_at__lte=data['date_to'])

        # Paginate
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ImageListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ImageListSerializer(queryset, many=True)
        return Response(serializer.data)


class ReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for Review management"""
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user_role = self.request.META.get('HTTP_X_USER_ROLE', 'customer')
        
        if user_role in ['validator', 'admin']:
            return self.queryset
        
        # Regular users can only see reviews of their own images
        user_id = self.request.META.get('HTTP_X_USER_ID')
        return self.queryset.filter(image__uploader_id=user_id)

    @action(detail=False, methods=['get'])
    def queue(self, request):
        """Get images pending review"""
        user_role = request.META.get('HTTP_X_USER_ROLE')
        
        if user_role not in ['validator', 'admin']:
            return Response(
                {'error': 'Only validators can access review queue'},
                status=status.HTTP_403_FORBIDDEN
            )

        images = Image.objects.filter(status__in=['submitted', 'in_review'])
        serializer = ImageListSerializer(images, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='(?P<image_id>[^/.]+)/approve')
    def approve(self, request, image_id=None):
        """Approve an image"""
        user_role = request.META.get('HTTP_X_USER_ROLE')
        user_id = request.META.get('HTTP_X_USER_ID')
        user_email = request.META.get('HTTP_X_USER_EMAIL')

        if user_role not in ['validator', 'admin']:
            return Response(
                {'error': 'Only validators can approve images'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            image = Image.objects.get(id=image_id)
        except Image.DoesNotExist:
            return Response(
                {'error': 'Image not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ReviewActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Update image status
        image.status = 'published'
        image.published_at = timezone.now()
        image.save()

        # Create review record
        review = Review.objects.create(
            image=image,
            reviewer_id=user_id,
            reviewer_email=user_email,
            status='approved',
            comment=serializer.validated_data.get('comment', ''),
            metadata_changes=serializer.validated_data.get('metadata_changes', {})
        )

        return Response({
            'message': 'Image approved',
            'review': ReviewSerializer(review).data
        })

    @action(detail=False, methods=['post'], url_path='(?P<image_id>[^/.]+)/reject')
    def reject(self, request, image_id=None):
        """Reject an image"""
        user_role = request.META.get('HTTP_X_USER_ROLE')
        user_id = request.META.get('HTTP_X_USER_ID')
        user_email = request.META.get('HTTP_X_USER_EMAIL')

        if user_role not in ['validator', 'admin']:
            return Response(
                {'error': 'Only validators can reject images'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            image = Image.objects.get(id=image_id)
        except Image.DoesNotExist:
            return Response(
                {'error': 'Image not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ReviewActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Update image status
        image.status = 'rejected'
        image.save()

        # Create review record
        review = Review.objects.create(
            image=image,
            reviewer_id=user_id,
            reviewer_email=user_email,
            status='rejected',
            comment=serializer.validated_data.get('comment', ''),
        )

        return Response({
            'message': 'Image rejected',
            'review': ReviewSerializer(review).data
        })


class UploadTaskViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for UploadTask (read-only)"""
    queryset = UploadTask.objects.all()
    serializer_class = UploadTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user_id = self.request.META.get('HTTP_X_USER_ID')
        user_role = self.request.META.get('HTTP_X_USER_ROLE')

        if user_role == 'admin':
            return self.queryset
        
        return self.queryset.filter(uploader_id=user_id)
