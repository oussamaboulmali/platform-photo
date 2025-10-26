"""
Models for order service - wallets, subscriptions, orders
"""
from django.db import models
from django.utils import timezone
from datetime import timedelta
import uuid


class UserWallet(models.Model):
    """User wallet for prepaid account balance"""
    user_id = models.IntegerField(unique=True, db_index=True)
    user_email = models.EmailField()
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default='DZD')  # Algerian Dinar
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_wallets'
        indexes = [
            models.Index(fields=['user_id']),
        ]

    def __str__(self):
        return f"{self.user_email} - {self.balance} {self.currency}"

    def add_balance(self, amount, description=''):
        """Add balance to wallet"""
        self.balance += amount
        self.save()
        
        # Create transaction record
        WalletTransaction.objects.create(
            wallet=self,
            transaction_type='credit',
            amount=amount,
            balance_after=self.balance,
            description=description
        )

    def deduct_balance(self, amount, description=''):
        """Deduct balance from wallet"""
        if self.balance < amount:
            raise ValueError("Insufficient balance")
        
        self.balance -= amount
        self.save()
        
        # Create transaction record
        WalletTransaction.objects.create(
            wallet=self,
            transaction_type='debit',
            amount=amount,
            balance_after=self.balance,
            description=description
        )

    def has_sufficient_balance(self, amount):
        """Check if wallet has sufficient balance"""
        return self.balance >= amount


class WalletTransaction(models.Model):
    """Transaction history for wallets"""
    TRANSACTION_TYPES = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    ]

    wallet = models.ForeignKey(UserWallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=500)
    reference = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wallet_transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wallet', 'created_at']),
        ]

    def __str__(self):
        return f"{self.wallet.user_email} - {self.transaction_type} - {self.amount}"


class TopUpRequest(models.Model):
    """Top-up requests (manual or via payment module)"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    user_id = models.IntegerField(db_index=True)
    user_email = models.EmailField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='DZD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Payment method (if payment module is used)
    payment_method = models.CharField(max_length=50, blank=True)  # eldhahabia, cib, algerie_poste
    payment_reference = models.CharField(max_length=200, blank=True)
    
    # Admin notes (for manual processing)
    admin_notes = models.TextField(blank=True)
    processed_by_id = models.IntegerField(null=True, blank=True)
    processed_by_email = models.EmailField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'topup_requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id', 'status']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.user_email} - {self.amount} {self.currency} - {self.status}"


class SubscriptionPlan(models.Model):
    """Subscription plans"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    duration_days = models.IntegerField()  # 30, 90, 180 for 1/3/6 months
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='DZD')
    
    # Quota/limits
    quota_credits = models.IntegerField(default=0)  # Number of downloads/purchases allowed
    quota_type = models.CharField(max_length=20, default='downloads')  # downloads, credits, unlimited
    
    # Features (JSON field for flexibility)
    features = models.JSONField(default=dict)
    
    is_active = models.BooleanField(default=True)
    is_trial = models.BooleanField(default=False)
    trial_days = models.IntegerField(default=0)
    
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscription_plans'
        ordering = ['order', 'duration_days']

    def __str__(self):
        return f"{self.name} ({self.duration_days} days)"


class UserSubscription(models.Model):
    """User subscriptions"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]

    user_id = models.IntegerField(db_index=True)
    user_email = models.EmailField()
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name='subscriptions')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    credits_remaining = models.IntegerField(default=0)
    
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)
    
    # Payment info
    payment_status = models.CharField(max_length=20, default='pending')
    payment_reference = models.CharField(max_length=200, blank=True)
    
    # Admin approval (if payment module disabled)
    approved_by_id = models.IntegerField(null=True, blank=True)
    approved_by_email = models.EmailField(blank=True)
    admin_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_subscriptions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id', 'status']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.user_email} - {self.plan.name} - {self.status}"

    def activate(self):
        """Activate subscription"""
        self.status = 'active'
        self.start_at = timezone.now()
        self.end_at = self.start_at + timedelta(days=self.plan.duration_days)
        self.credits_remaining = self.plan.quota_credits
        self.save()

    def is_valid(self):
        """Check if subscription is valid"""
        if self.status != 'active':
            return False
        if self.end_at and timezone.now() > self.end_at:
            self.status = 'expired'
            self.save()
            return False
        return True

    def has_credits(self, amount=1):
        """Check if subscription has enough credits"""
        if self.plan.quota_type == 'unlimited':
            return True
        return self.credits_remaining >= amount

    def use_credits(self, amount=1):
        """Use subscription credits"""
        if self.plan.quota_type == 'unlimited':
            return True
        if self.credits_remaining >= amount:
            self.credits_remaining -= amount
            self.save()
            return True
        return False


class Order(models.Model):
    """Orders for image purchases"""
    LICENSE_TYPES = [
        ('standard', 'Standard License'),
        ('extended', 'Extended License'),
        ('exclusive', 'Exclusive License'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_METHODS = [
        ('wallet', 'Account Wallet'),
        ('subscription', 'Subscription'),
        ('manual', 'Manual Payment'),
    ]

    order_number = models.CharField(max_length=50, unique=True, db_index=True)
    
    # User info
    user_id = models.IntegerField(db_index=True)
    user_email = models.EmailField()
    
    # Image info (denormalized for history)
    image_id = models.IntegerField(db_index=True)
    image_filename = models.CharField(max_length=500)
    
    # License and pricing
    license_type = models.CharField(max_length=20, choices=LICENSE_TYPES, default='standard')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='DZD')
    
    # Payment
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='wallet')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_reference = models.CharField(max_length=200, blank=True)
    
    # Download token
    download_token = models.UUIDField(default=uuid.uuid4, unique=True)
    download_expires_at = models.DateTimeField(null=True, blank=True)
    download_count = models.IntegerField(default=0)
    max_downloads = models.IntegerField(default=3)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id', 'created_at']),
            models.Index(fields=['order_number']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['download_token']),
        ]

    def __str__(self):
        return f"{self.order_number} - {self.user_email} - {self.payment_status}"

    @staticmethod
    def generate_order_number():
        """Generate unique order number"""
        import random
        import string
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"ORD-{timestamp}-{random_str}"

    def set_download_expiry(self, hours=24):
        """Set download token expiry"""
        self.download_expires_at = timezone.now() + timedelta(hours=hours)
        self.save()

    def is_download_valid(self):
        """Check if download is still valid"""
        if self.payment_status != 'paid':
            return False
        if self.download_count >= self.max_downloads:
            return False
        if self.download_expires_at and timezone.now() > self.download_expires_at:
            return False
        return True

    def increment_download_count(self):
        """Increment download count"""
        self.download_count += 1
        self.save()


class PaymentLog(models.Model):
    """Payment logs for reconciliation (payment module)"""
    LOG_TYPES = [
        ('webhook', 'Webhook'),
        ('manual', 'Manual'),
        ('system', 'System'),
    ]

    log_type = models.CharField(max_length=20, choices=LOG_TYPES)
    provider = models.CharField(max_length=50)  # eldhahabia, cib, algerie_poste
    reference = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='DZD')
    
    # Related entities
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='payment_logs')
    topup_request = models.ForeignKey(TopUpRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='payment_logs')
    
    # Raw data
    payload = models.JSONField(default=dict)
    response = models.JSONField(default=dict)
    
    status = models.CharField(max_length=20)
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payment_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reference']),
            models.Index(fields=['provider']),
        ]

    def __str__(self):
        return f"{self.provider} - {self.reference} - {self.status}"
