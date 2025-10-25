"""Models for blocs and ads management"""
from django.db import models


class Bloc(models.Model):
    """Frontend blocs/blocks for homepage and pages"""
    BLOC_TYPES = [
        ('a_la_une', 'À la une'),
        ('ad_slot', 'Ad Slot'),
        ('category_block', 'Category Block'),
        ('topic_block', 'Topic Block'),
        ('places_block', 'Places Block'),
        ('custom', 'Custom Block'),
    ]

    SOURCE_TYPES = [
        ('manual', 'Manual Selection'),
        ('category', 'Category'),
        ('topic', 'Topic'),
        ('place', 'Place'),
        ('latest', 'Latest Images'),
        ('popular', 'Popular Images'),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    type = models.CharField(max_length=30, choices=BLOC_TYPES)
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES, default='manual')
    source_id = models.IntegerField(null=True, blank=True)
    
    visible = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    # Scheduling
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)
    
    # Configuration
    config = models.JSONField(default=dict, blank=True)
    max_items = models.IntegerField(default=10)
    
    # Page placement
    page_locations = models.JSONField(default=list, blank=True)  # ['homepage', 'search', 'category']
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'blocs'
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['visible', 'order']),
            models.Index(fields=['type']),
        ]

    def __str__(self):
        return f"{self.name} ({self.type})"


class BlocItem(models.Model):
    """Manual items in blocs"""
    bloc = models.ForeignKey(Bloc, on_delete=models.CASCADE, related_name='items')
    image_id = models.IntegerField()
    order = models.IntegerField(default=0)
    title_override = models.CharField(max_length=500, blank=True)
    description_override = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bloc_items'
        ordering = ['order']
        unique_together = ['bloc', 'image_id']

    def __str__(self):
        return f"{self.bloc.name} - Image {self.image_id}"


class AdSlot(models.Model):
    """Advertisement slots"""
    AD_TYPES = [
        ('image', 'Image Ad'),
        ('link', 'Link Ad'),
        ('html', 'HTML Ad'),
    ]

    POSITIONS = [
        ('header', 'Header'),
        ('sidebar', 'Sidebar'),
        ('footer', 'Footer'),
        ('inline', 'Inline Content'),
        ('modal', 'Modal/Popup'),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    type = models.CharField(max_length=20, choices=AD_TYPES, default='image')
    position = models.CharField(max_length=20, choices=POSITIONS, default='sidebar')
    
    # Content
    content_type = models.CharField(max_length=20, default='image')
    target_url = models.URLField(blank=True)
    image_path = models.CharField(max_length=1000, blank=True)
    html_content = models.TextField(blank=True)
    
    # Display settings
    active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)
    max_impressions = models.IntegerField(null=True, blank=True)
    current_impressions = models.IntegerField(default=0)
    
    # Scheduling
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)
    
    # Targeting
    page_targets = models.JSONField(default=list, blank=True)  # ['homepage', 'search']
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'ad_slots'
        ordering = ['priority', 'name']
        indexes = [
            models.Index(fields=['active', 'priority']),
            models.Index(fields=['position']),
        ]

    def __str__(self):
        return f"{self.name} ({self.position})"

    def increment_impressions(self):
        """Increment impression count"""
        self.current_impressions += 1
        if self.max_impressions and self.current_impressions >= self.max_impressions:
            self.active = False
        self.save()
