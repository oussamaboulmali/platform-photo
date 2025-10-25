"""
Celery tasks for image processing
"""
from celery import shared_task
from django.conf import settings
from PIL import Image, ImageDraw, ImageFont
import pyvips
import os
from datetime import datetime, timedelta
from .models import Image as ImageModel, ImageDerivative, UploadTask


@shared_task
def create_derivatives(image_id):
    """
    Create image derivatives (thumbnail, preview, medium)
    """
    try:
        image = ImageModel.objects.get(id=image_id)
        original_path = os.path.join(settings.STORAGE_ROOT, image.file_path)
        
        if not os.path.exists(original_path):
            raise FileNotFoundError(f"Original image not found: {original_path}")
        
        # Use pyvips for efficient image processing
        vips_image = pyvips.Image.new_from_file(original_path, access='sequential')
        
        # Create thumbnail (200px)
        thumbnail_path = create_derivative(
            vips_image, 
            image, 
            'thumbnail', 
            settings.THUMBNAIL_SIZE,
            watermark=False
        )
        
        # Create watermarked preview (1024px)
        preview_path = create_derivative(
            vips_image, 
            image, 
            'preview', 
            settings.PREVIEW_SIZE,
            watermark=True
        )
        
        # Create medium (2048px)
        medium_path = create_derivative(
            vips_image, 
            image, 
            'medium', 
            settings.MEDIUM_SIZE,
            watermark=False
        )
        
        # Store original reference
        ImageDerivative.objects.update_or_create(
            image=image,
            kind='original',
            defaults={
                'file_path': image.file_path,
                'width': image.width,
                'height': image.height,
                'filesize': image.filesize,
                'is_watermarked': False,
            }
        )
        
        return {
            'success': True,
            'image_id': image_id,
            'derivatives': ['thumbnail', 'preview', 'medium', 'original']
        }
        
    except Exception as e:
        return {
            'success': False,
            'image_id': image_id,
            'error': str(e)
        }


def create_derivative(vips_image, image, kind, max_size, watermark=False):
    """
    Create a single derivative using pyvips
    """
    # Calculate new dimensions maintaining aspect ratio
    width = vips_image.width
    height = vips_image.height
    
    if width > height:
        new_width = min(width, max_size)
        new_height = int(height * (new_width / width))
    else:
        new_height = min(height, max_size)
        new_width = int(width * (new_height / height))
    
    # Resize image
    scale = new_width / width
    resized = vips_image.resize(scale)
    
    # Generate file path
    base_name, ext = os.path.splitext(image.filename)
    derivative_filename = f"{base_name}_{kind}{ext}"
    derivative_rel_path = os.path.join(
        os.path.dirname(image.file_path),
        derivative_filename
    )
    derivative_path = os.path.join(settings.STORAGE_ROOT, derivative_rel_path)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(derivative_path), exist_ok=True)
    
    # Save image
    resized.write_to_file(derivative_path, Q=85)
    
    # Apply watermark if needed
    if watermark:
        apply_watermark_pillow(derivative_path)
    
    # Get file size
    filesize = os.path.getsize(derivative_path)
    
    # Save derivative record
    ImageDerivative.objects.update_or_create(
        image=image,
        kind=kind,
        defaults={
            'file_path': derivative_rel_path,
            'width': new_width,
            'height': new_height,
            'filesize': filesize,
            'is_watermarked': watermark,
        }
    )
    
    return derivative_path


def apply_watermark_pillow(image_path):
    """
    Apply watermark to image using Pillow
    """
    try:
        with Image.open(image_path) as img:
            # Create watermark
            draw = ImageDraw.Draw(img)
            watermark_text = settings.WATERMARK_TEXT
            
            # Calculate position (diagonal pattern)
            width, height = img.size
            
            # Try to load a font, fallback to default
            try:
                font_size = int(min(width, height) * 0.05)
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # Create semi-transparent overlay
            overlay = Image.new('RGBA', img.size, (255, 255, 255, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            
            # Add watermarks in a diagonal pattern
            spacing_x = width // 3
            spacing_y = height // 3
            
            for y in range(0, height, spacing_y):
                for x in range(0, width, spacing_x):
                    # Add text with transparency
                    overlay_draw.text(
                        (x, y),
                        watermark_text,
                        fill=(255, 255, 255, 128),
                        font=font
                    )
            
            # Composite the overlay onto the original image
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            watermarked = Image.alpha_composite(img, overlay)
            
            # Convert back to RGB if needed
            if watermarked.mode == 'RGBA':
                watermarked = watermarked.convert('RGB')
            
            # Save
            watermarked.save(image_path, quality=85, optimize=True)
            
    except Exception as e:
        print(f"Error applying watermark: {e}")


@shared_task
def process_upload(upload_task_id):
    """
    Process an uploaded file
    """
    try:
        upload_task = UploadTask.objects.get(id=upload_task_id)
        upload_task.status = 'processing'
        upload_task.save()
        
        file_path = upload_task.file_path
        full_path = os.path.join(settings.STORAGE_ROOT, file_path)
        
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Upload file not found: {full_path}")
        
        # Calculate MD5
        md5 = ImageModel.calculate_md5(full_path)
        
        # Check for duplicates
        existing = ImageModel.objects.filter(md5=md5).first()
        if existing:
            upload_task.status = 'failed'
            upload_task.error_message = 'Duplicate image already exists'
            upload_task.save()
            return {'success': False, 'error': 'Duplicate image'}
        
        # Get image dimensions
        vips_image = pyvips.Image.new_from_file(full_path)
        width = vips_image.width
        height = vips_image.height
        filesize = os.path.getsize(full_path)
        
        # Create image record
        image = ImageModel.objects.create(
            uploader_id=upload_task.uploader_id,
            uploader_email='',  # Will be populated by the API
            filename=upload_task.original_filename,
            file_path=file_path,
            type='photo',
            status='draft',
            md5=md5,
            width=width,
            height=height,
            orientation='landscape' if width > height else ('portrait' if height > width else 'square'),
            filesize=filesize,
            mime_type='image/jpeg',
        )
        
        # Update upload task
        upload_task.status = 'completed'
        upload_task.image = image
        upload_task.finished_at = datetime.now()
        upload_task.save()
        
        # Trigger derivative creation
        create_derivatives.delay(image.id)
        
        return {'success': True, 'image_id': image.id}
        
    except Exception as e:
        upload_task.status = 'failed'
        upload_task.error_message = str(e)
        upload_task.finished_at = datetime.now()
        upload_task.save()
        return {'success': False, 'error': str(e)}


@shared_task
def reindex_search(image_id):
    """
    Reindex image for full-text search
    """
    from django.contrib.postgres.search import SearchVector
    
    try:
        image = ImageModel.objects.get(id=image_id)
        
        # Get metadata
        metadata = image.metadata.filter(language='en').first()
        if metadata:
            # Create search vector from title, caption, and keywords
            keywords_text = ' '.join(metadata.keywords) if metadata.keywords else ''
            search_text = f"{metadata.title} {metadata.caption} {keywords_text}"
            
            image.search_vector = SearchVector('filename') + SearchVector(models.Value(search_text))
            image.save(update_fields=['search_vector'])
        
        return {'success': True, 'image_id': image_id}
    except Exception as e:
        return {'success': False, 'image_id': image_id, 'error': str(e)}


@shared_task
def expire_download_tokens():
    """
    Expire old download tokens (called periodically)
    """
    # This will be implemented in order service
    # For now, just a placeholder
    return {'success': True, 'message': 'Download token expiration task'}


@shared_task
def archive_old_images():
    """
    Move old published images to archive storage
    """
    try:
        # Archive images older than 1 year that are published
        archive_date = datetime.now() - timedelta(days=365)
        images_to_archive = ImageModel.objects.filter(
            status='published',
            published_at__lt=archive_date
        )
        
        archived_count = 0
        for image in images_to_archive:
            # Move file to archive
            original_path = os.path.join(settings.STORAGE_ROOT, image.file_path)
            archive_path = os.path.join(settings.STORAGE_ARCHIVE_ROOT, image.file_path)
            
            if os.path.exists(original_path):
                os.makedirs(os.path.dirname(archive_path), exist_ok=True)
                os.rename(original_path, archive_path)
                
                # Update image record
                image.status = 'archived'
                image.file_path = os.path.join('archive', image.file_path)
                image.save()
                
                archived_count += 1
        
        return {'success': True, 'archived_count': archived_count}
    except Exception as e:
        return {'success': False, 'error': str(e)}
