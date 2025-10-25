"""
Admin configuration for orders app
"""
from django.contrib import admin
from .models import (
    UserWallet, WalletTransaction, TopUpRequest,
    SubscriptionPlan, UserSubscription, Order, PaymentLog
)


@admin.register(UserWallet)
class UserWalletAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'balance', 'currency', 'is_active', 'updated_at']
    search_fields = ['user_email', 'user_id']
    list_filter = ['is_active', 'currency']


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ['wallet', 'transaction_type', 'amount', 'balance_after', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['wallet__user_email', 'reference']


@admin.register(TopUpRequest)
class TopUpRequestAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'amount', 'status', 'created_at', 'processed_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['user_email', 'payment_reference']
    actions = ['approve_topups']

    def approve_topups(self, request, queryset):
        for topup in queryset.filter(status='pending'):
            from .views import UserWallet
            wallet, _ = UserWallet.objects.get_or_create(
                user_id=topup.user_id,
                defaults={'user_email': topup.user_email}
            )
            wallet.add_balance(topup.amount, f"Top-up: {topup.id}")
            topup.status = 'completed'
            topup.save()
        self.message_user(request, "Top-ups approved")
    approve_topups.short_description = "Approve selected top-ups"


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'duration_days', 'price', 'quota_credits', 'is_active', 'order']
    list_filter = ['is_active', 'is_trial']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'plan', 'status', 'credits_remaining', 'start_at', 'end_at']
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['user_email', 'payment_reference']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user_email', 'image_filename', 'amount', 'payment_status', 'created_at']
    list_filter = ['payment_status', 'license_type', 'payment_method', 'created_at']
    search_fields = ['order_number', 'user_email', 'image_filename']


@admin.register(PaymentLog)
class PaymentLogAdmin(admin.ModelAdmin):
    list_display = ['provider', 'reference', 'amount', 'status', 'created_at']
    list_filter = ['provider', 'log_type', 'status', 'created_at']
    search_fields = ['reference']
