"""
Views for Order service
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings
from django.utils import timezone
from django.db import transaction as db_transaction
import requests
from .models import (
    UserWallet, WalletTransaction, TopUpRequest,
    SubscriptionPlan, UserSubscription, Order, PaymentLog
)
from .serializers import (
    UserWalletSerializer, WalletTransactionSerializer, TopUpRequestSerializer,
    SubscriptionPlanSerializer, UserSubscriptionSerializer,
    OrderSerializer, CreateOrderSerializer, PaymentLogSerializer
)


class UserWalletViewSet(viewsets.ModelViewSet):
    queryset = UserWallet.objects.all()
    serializer_class = UserWalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user_id = self.request.META.get('HTTP_X_USER_ID')
        user_role = self.request.META.get('HTTP_X_USER_ROLE')

        if user_role == 'admin':
            return self.queryset
        return self.queryset.filter(user_id=user_id)

    @action(detail=False, methods=['get'])
    def my_wallet(self, request):
        """Get current user's wallet"""
        user_id = request.META.get('HTTP_X_USER_ID')
        user_email = request.META.get('HTTP_X_USER_EMAIL')

        wallet, created = UserWallet.objects.get_or_create(
            user_id=user_id,
            defaults={'user_email': user_email}
        )
        
        return Response(UserWalletSerializer(wallet).data)

    @action(detail=False, methods=['get'])
    def my_transactions(self, request):
        """Get current user's wallet transactions"""
        user_id = request.META.get('HTTP_X_USER_ID')
        
        wallet = UserWallet.objects.filter(user_id=user_id).first()
        if not wallet:
            return Response({'transactions': []})

        transactions = wallet.transactions.all()[:50]
        return Response(WalletTransactionSerializer(transactions, many=True).data)


class TopUpRequestViewSet(viewsets.ModelViewSet):
    queryset = TopUpRequest.objects.all()
    serializer_class = TopUpRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user_id = self.request.META.get('HTTP_X_USER_ID')
        user_role = self.request.META.get('HTTP_X_USER_ROLE')

        if user_role == 'admin':
            return self.queryset
        return self.queryset.filter(user_id=user_id)

    def create(self, request, *args, **kwargs):
        """Create a top-up request"""
        user_id = request.META.get('HTTP_X_USER_ID')
        user_email = request.META.get('HTTP_X_USER_EMAIL')

        amount = request.data.get('amount')
        if not amount or float(amount) <= 0:
            return Response({'error': 'Invalid amount'}, status=status.HTTP_400_BAD_REQUEST)

        topup = TopUpRequest.objects.create(
            user_id=user_id,
            user_email=user_email,
            amount=amount,
            payment_method=request.data.get('payment_method', ''),
            status='pending'
        )

        return Response(
            TopUpRequestSerializer(topup).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a top-up request (admin only)"""
        user_role = request.META.get('HTTP_X_USER_ROLE')
        if user_role != 'admin':
            return Response({'error': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)

        topup = self.get_object()
        if topup.status != 'pending':
            return Response({'error': 'Only pending requests can be approved'}, 
                          status=status.HTTP_400_BAD_REQUEST)

        with db_transaction.atomic():
            # Get or create wallet
            wallet, _ = UserWallet.objects.get_or_create(
                user_id=topup.user_id,
                defaults={'user_email': topup.user_email}
            )

            # Add balance
            wallet.add_balance(topup.amount, f"Top-up: {topup.id}")

            # Update top-up request
            topup.status = 'completed'
            topup.processed_by_id = request.META.get('HTTP_X_USER_ID')
            topup.processed_by_email = request.META.get('HTTP_X_USER_EMAIL')
            topup.processed_at = timezone.now()
            topup.admin_notes = request.data.get('admin_notes', '')
            topup.save()

        return Response({'message': 'Top-up approved', 'wallet': UserWalletSerializer(wallet).data})


class SubscriptionPlanViewSet(viewsets.ModelViewSet):
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]  # Admin check should be added
        return [permissions.AllowAny()]


class UserSubscriptionViewSet(viewsets.ModelViewSet):
    queryset = UserSubscription.objects.all()
    serializer_class = UserSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user_id = self.request.META.get('HTTP_X_USER_ID')
        user_role = self.request.META.get('HTTP_X_USER_ROLE')

        if user_role == 'admin':
            return self.queryset
        return self.queryset.filter(user_id=user_id)

    @action(detail=False, methods=['get'])
    def my_subscriptions(self, request):
        """Get current user's subscriptions"""
        user_id = request.META.get('HTTP_X_USER_ID')
        subscriptions = self.queryset.filter(user_id=user_id)
        return Response(UserSubscriptionSerializer(subscriptions, many=True).data)

    @action(detail=False, methods=['post'])
    def subscribe(self, request):
        """Subscribe to a plan"""
        user_id = request.META.get('HTTP_X_USER_ID')
        user_email = request.META.get('HTTP_X_USER_EMAIL')
        plan_id = request.data.get('plan_id')

        try:
            plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if payment module is enabled
        if settings.PAYMENT_MODULE_ENABLED:
            # TODO: Integrate with payment provider
            payment_status = 'pending'
            subscription_status = 'pending'
        else:
            # Manual approval required
            payment_status = 'pending'
            subscription_status = 'pending'

        subscription = UserSubscription.objects.create(
            user_id=user_id,
            user_email=user_email,
            plan=plan,
            status=subscription_status,
            payment_status=payment_status
        )

        return Response({
            'message': 'Subscription request created. Admin approval required.',
            'subscription': UserSubscriptionSerializer(subscription).data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a subscription (admin only)"""
        user_role = request.META.get('HTTP_X_USER_ROLE')
        if user_role != 'admin':
            return Response({'error': 'Admin only'}, status=status.HTTP_403_FORBIDDEN)

        subscription = self.get_object()
        if subscription.status != 'pending':
            return Response({'error': 'Only pending subscriptions can be approved'},
                          status=status.HTTP_400_BAD_REQUEST)

        subscription.activate()
        subscription.approved_by_id = request.META.get('HTTP_X_USER_ID')
        subscription.approved_by_email = request.META.get('HTTP_X_USER_EMAIL')
        subscription.admin_notes = request.data.get('admin_notes', '')
        subscription.save()

        return Response({
            'message': 'Subscription approved',
            'subscription': UserSubscriptionSerializer(subscription).data
        })


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user_id = self.request.META.get('HTTP_X_USER_ID')
        user_role = self.request.META.get('HTTP_X_USER_ROLE')

        if user_role == 'admin':
            return self.queryset
        return self.queryset.filter(user_id=user_id)

    @action(detail=False, methods=['post'])
    def create_order(self, request):
        """Create an order for image purchase"""
        serializer = CreateOrderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_id = request.META.get('HTTP_X_USER_ID')
        user_email = request.META.get('HTTP_X_USER_EMAIL')

        image_id = serializer.validated_data['image_id']
        license_type = serializer.validated_data['license_type']
        payment_method = serializer.validated_data['payment_method']

        # Get image details from image service
        try:
            image_response = requests.get(
                f"{settings.IMAGE_SERVICE_URL}/api/images/{image_id}/",
                headers={'Authorization': request.META.get('HTTP_AUTHORIZATION', '')}
            )
            if image_response.status_code != 200:
                return Response({'error': 'Image not found'}, status=status.HTTP_404_NOT_FOUND)
            image_data = image_response.json()
        except Exception as e:
            return Response({'error': 'Failed to fetch image'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Calculate price (simplified - should be configurable)
        price_map = {'standard': 500, 'extended': 1500, 'exclusive': 5000}
        amount = price_map.get(license_type, 500)

        with db_transaction.atomic():
            # Create order
            order = Order.objects.create(
                order_number=Order.generate_order_number(),
                user_id=user_id,
                user_email=user_email,
                image_id=image_id,
                image_filename=image_data.get('filename', ''),
                license_type=license_type,
                amount=amount,
                payment_method=payment_method,
                payment_status='pending'
            )

            # Process payment
            if payment_method == 'wallet':
                wallet = UserWallet.objects.filter(user_id=user_id).first()
                if not wallet or not wallet.has_sufficient_balance(amount):
                    return Response({'error': 'Insufficient balance'}, 
                                  status=status.HTTP_400_BAD_REQUEST)

                wallet.deduct_balance(amount, f"Order: {order.order_number}")
                order.payment_status = 'paid'
                order.completed_at = timezone.now()
                order.set_download_expiry(hours=24)
                order.save()

            elif payment_method == 'subscription':
                subscription = UserSubscription.objects.filter(
                    user_id=user_id,
                    status='active'
                ).first()

                if not subscription or not subscription.is_valid():
                    return Response({'error': 'No active subscription'}, 
                                  status=status.HTTP_400_BAD_REQUEST)

                if not subscription.has_credits(1):
                    return Response({'error': 'Insufficient subscription credits'}, 
                                  status=status.HTTP_400_BAD_REQUEST)

                subscription.use_credits(1)
                order.payment_status = 'paid'
                order.payment_reference = f"Subscription: {subscription.id}"
                order.completed_at = timezone.now()
                order.set_download_expiry(hours=24)
                order.save()

        return Response({
            'message': 'Order created successfully',
            'order': OrderSerializer(order).data
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='download/(?P<token>[^/.]+)')
    def download(self, request, token=None):
        """Download image using download token"""
        try:
            order = Order.objects.get(download_token=token)
        except Order.DoesNotExist:
            return Response({'error': 'Invalid token'}, status=status.HTTP_404_NOT_FOUND)

        if not order.is_download_valid():
            return Response({'error': 'Download token expired or limit reached'}, 
                          status=status.HTTP_403_FORBIDDEN)

        order.increment_download_count()

        return Response({
            'message': 'Download authorized',
            'image_id': order.image_id,
            'downloads_remaining': order.max_downloads - order.download_count
        })


class PaymentLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PaymentLog.objects.all()
    serializer_class = PaymentLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user_role = self.request.META.get('HTTP_X_USER_ROLE')
        if user_role == 'admin':
            return self.queryset
        return self.queryset.none()
