"""
Serializers for Order service
"""
from rest_framework import serializers
from .models import (
    UserWallet, WalletTransaction, TopUpRequest,
    SubscriptionPlan, UserSubscription, Order, PaymentLog
)


class UserWalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserWallet
        fields = '__all__'
        read_only_fields = ['id', 'balance', 'created_at', 'updated_at']


class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class TopUpRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = TopUpRequest
        fields = '__all__'
        read_only_fields = ['id', 'status', 'processed_by_id', 'processed_by_email', 'processed_at', 'created_at']


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    plan_details = SubscriptionPlanSerializer(source='plan', read_only=True)

    class Meta:
        model = UserSubscription
        fields = '__all__'
        read_only_fields = ['id', 'status', 'credits_remaining', 'start_at', 'end_at', 
                           'approved_by_id', 'approved_by_email', 'created_at', 'updated_at']


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['id', 'order_number', 'download_token', 'download_count', 
                           'created_at', 'completed_at']


class CreateOrderSerializer(serializers.Serializer):
    image_id = serializers.IntegerField()
    license_type = serializers.ChoiceField(choices=['standard', 'extended', 'exclusive'])
    payment_method = serializers.ChoiceField(choices=['wallet', 'subscription'])


class PaymentLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentLog
        fields = '__all__'
        read_only_fields = ['id', 'created_at']
