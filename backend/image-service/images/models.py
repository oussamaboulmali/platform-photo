"""
Image models for image service
"""
from django.db import models
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex
import hashlib
import os
from datetime import datetime


class Category(models.Model):
    """Hierarchical category for images"""
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'categories'
        ordering = ['order', 'name']
        verbose_name_plural = 'categories'
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['parent']),
        ]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    def get_full_path(self):
        """Get full category path"""
        if self.parent:
            return f"{self.parent.get_full_path()} > {self.name}"
        return self.name


class Topic(models.Model):
    """Topics for image classification"""
    TOPIC_TYPES = [
        ('event', 'Event'),
        ('document', 'Document'),
        ('top_shot', 'Top Shot'),
        ('custom', 'Custom'),
    ]

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    type = models.CharField(max_length=20, choices=TOPIC_TYPES, default='custom')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'topics'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.type})"


class Place(models.Model):
    """Geographic places for images"""
    PLACE_TYPES = [
        ('city', 'City'),
        ('venue', 'Venue'),
        ('country', 'Country'),
        ('region', 'Region'),
        ('custom', 'Custom'),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    type = models.CharField(max_length=20, choices=PLACE_TYPES, default='custom')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'places'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.type})"


class Image(models.Model):
    """Main image model"""
    IMAGE_TYPES = [
        ('photo', 'Photo'),
        ('infographie', 'Infographie'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('in_review', 'In Review'),
        ('rejected', 'Rejected'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    ORIENTATION_CHOICES = [
        ('landscape', 'Landscape'),
        ('portrait', 'Portrait'),
        ('square', 'Square'),
    ]

    # User reference (stored as integer, references auth service)
    uploader_id = models.IntegerField(db_index=True)
    uploader_email = models.EmailField()  # Denormalized for easier querying

    # File information
    filename = models.CharField(max_length=500)
    file_path = models.CharField(max_length=1000)
    type = models.CharField(max_length=20, choices=IMAGE_TYPES, default='photo')
    
    # Status and workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Image metadata
    md5 = models.CharField(max_length=32, unique=True, db_index=True)
    width = models.IntegerField()
    height = models.IntegerField()
    orientation = models.CharField(max_length=20, choices=ORIENTATION_CHOICES)
    filesize = models.BigIntegerField()  # in bytes
    mime_type = models.CharField(max_length=100)
    
    # Taxonomy
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='images')
    topics = models.ManyToManyField(Topic, related_name='images', blank=True)
    places = models.ManyToManyField(Place, related_name='images', blank=True)
    
    # Search
    search_vector = SearchVectorField(null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # Stats
    view_count = models.IntegerField(default=0)
    download_count = models.IntegerField(default=0)
    purchase_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'images'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['uploader_id']),
            models.Index(fields=['status']),
            models.Index(fields=['type']),
            models.Index(fields=['md5']),
            models.Index(fields=['created_at']),
            models.Index(fields=['published_at']),
            GinIndex(fields=['search_vector']),
        ]

    def __str__(self):
        return f"{self.filename} ({self.status})"

    def calculate_orientation(self):
        """Calculate image orientation based on dimensions"""
        if self.width > self.height:
            return 'landscape'
        elif self.width < self.height:
            return 'portrait'
        else:
            return 'square'

    @staticmethod
    def calculate_md5(file_path):
        """Calculate MD5 hash of file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def get_storage_path(self):
        """Get storage path for image"""
        date = self.created_at or datetime.now()
        return os.path.join(
            str(date.year),
            f"{date.month:02d}",
            f"user_{self.uploader_id}",
            self.filename
        )


class ImageDerivative(models.Model):
    """Image derivatives (thumbnails, previews, etc.)"""
    DERIVATIVE_KINDS = [
        ('thumbnail', 'Thumbnail'),
        ('preview', 'Preview'),
        ('medium', 'Medium'),
        ('original', 'Original'),
    ]

    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='derivatives')
    kind = models.CharField(max_length=20, choices=DERIVATIVE_KINDS)
    file_path = models.CharField(max_length=1000)
    width = models.IntegerField()
    height = models.IntegerField()
    filesize = models.BigIntegerField()
    is_watermarked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'image_derivatives'
        unique_together = ['image', 'kind']
        indexes = [
            models.Index(fields=['image', 'kind']),
        ]

    def __str__(self):
        return f"{self.image.filename} - {self.kind}"


class ImageMetadata(models.Model):
    """Multilingual metadata for images"""
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('fr', 'French'),
        ('ar', 'Arabic'),
    ]

    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='metadata')
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='en')
    title = models.CharField(max_length=500)
    caption = models.TextField(blank=True)
    keywords = models.JSONField(default=list)  # Array of keywords
    alt_text = models.CharField(max_length=500, blank=True)
    
    # Additional metadata
    photographer_name = models.CharField(max_length=200, blank=True)
    copyright_info = models.CharField(max_length=500, blank=True)
    capture_date = models.DateTimeField(null=True, blank=True)
    camera_model = models.CharField(max_length=200, blank=True)
    lens_model = models.CharField(max_length=200, blank=True)
    iso = models.IntegerField(null=True, blank=True)
    aperture = models.CharField(max_length=20, blank=True)
    shutter_speed = models.CharField(max_length=20, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'image_metadata'
        unique_together = ['image', 'language']

    def __str__(self):
        return f"{self.title} ({self.language})"


class Review(models.Model):
    """Review records for image validation"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='reviews')
    reviewer_id = models.IntegerField(db_index=True)
    reviewer_email = models.EmailField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    comment = models.TextField(blank=True)
    metadata_changes = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reviews'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['image', 'status']),
            models.Index(fields=['reviewer_id']),
        ]

    def __str__(self):
        return f"Review of {self.image.filename} by {self.reviewer_email} - {self.status}"


class UploadTask(models.Model):
    """Track upload tasks for async processing"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    uploader_id = models.IntegerField(db_index=True)
    original_filename = models.CharField(max_length=500)
    file_path = models.CharField(max_length=1000)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    image = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'upload_tasks'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['uploader_id']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.original_filename} - {self.status}"
