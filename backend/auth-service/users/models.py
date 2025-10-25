"""
User models for authentication service
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
import pyotp
import qrcode
from io import BytesIO
import base64


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser
    """
    ROLE_CHOICES = [
        ('photographer', 'Photographer'),
        ('infographiste', 'Infographiste'),
        ('validator', 'Validator'),
        ('admin', 'Admin'),
        ('customer', 'Customer'),
    ]

    email = models.EmailField(unique=True, db_index=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    two_fa_enabled = models.BooleanField(default=False)
    two_fa_secret = models.CharField(max_length=32, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_image = models.CharField(max_length=500, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.email} ({self.role})"

    def generate_2fa_secret(self):
        """Generate a new 2FA secret"""
        if not self.two_fa_secret:
            self.two_fa_secret = pyotp.random_base32()
            self.save()
        return self.two_fa_secret

    def get_2fa_uri(self):
        """Get the 2FA provisioning URI for QR code"""
        secret = self.two_fa_secret or self.generate_2fa_secret()
        return pyotp.totp.TOTP(secret).provisioning_uri(
            name=self.email,
            issuer_name="Agency Platform"
        )

    def verify_2fa_token(self, token):
        """Verify a 2FA token"""
        if not self.two_fa_secret:
            return False
        totp = pyotp.TOTP(self.two_fa_secret)
        return totp.verify(token, valid_window=1)

    def get_2fa_qr_code(self):
        """Generate QR code for 2FA setup"""
        uri = self.get_2fa_uri()
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"

    def has_permission(self, permission):
        """Check if user has a specific permission based on role"""
        role_permissions = {
            'admin': ['*'],  # All permissions
            'validator': ['validate_images', 'edit_metadata', 'view_all_images'],
            'photographer': ['upload_images', 'edit_own_images', 'view_own_images'],
            'infographiste': ['upload_infographics', 'edit_own_infographics', 'view_own_images'],
            'customer': ['browse_images', 'purchase_images', 'download_purchased'],
        }
        
        user_perms = role_permissions.get(self.role, [])
        return '*' in user_perms or permission in user_perms


class PhotographerProfile(models.Model):
    """
    Extended profile for photographers and infographistes
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='photographer_profile')
    display_name = models.CharField(max_length=100)
    bio = models.TextField(blank=True)
    website = models.URLField(blank=True, null=True)
    contact_info = models.JSONField(default=dict, blank=True)
    
    # Statistics
    total_uploads = models.IntegerField(default=0)
    total_approved = models.IntegerField(default=0)
    total_rejected = models.IntegerField(default=0)
    total_downloads = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'photographer_profiles'

    def __str__(self):
        return f"{self.display_name} - {self.user.email}"


class AuditLog(models.Model):
    """
    Audit log for tracking user actions
    """
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('purchase', 'Purchase'),
        ('download', 'Download'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    target_type = models.CharField(max_length=50)  # e.g., 'image', 'order', 'user'
    target_id = models.CharField(max_length=100)
    payload = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['target_type', 'target_id']),
            models.Index(fields=['action']),
        ]

    def __str__(self):
        return f"{self.user} - {self.action} - {self.target_type}:{self.target_id}"
