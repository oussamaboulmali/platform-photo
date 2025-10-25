"""
Views for User authentication and management
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login, logout
from django.utils import timezone
from .models import User, PhotographerProfile, AuditLog
from .serializers import (
    UserSerializer, UserRegistrationSerializer, LoginSerializer,
    TwoFactorSetupSerializer, TwoFactorVerifySerializer,
    PasswordChangeSerializer, PhotographerProfileSerializer,
    AuditLogSerializer
)
from .permissions import IsAdmin, IsOwnerOrAdmin


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def create_audit_log(user, action, target_type, target_id, payload=None, request=None):
    """Create an audit log entry"""
    log_data = {
        'user': user,
        'action': action,
        'target_type': target_type,
        'target_id': str(target_id),
        'payload': payload or {},
    }
    
    if request:
        log_data['ip_address'] = get_client_ip(request)
        log_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
    
    return AuditLog.objects.create(**log_data)


class AuthViewSet(viewsets.GenericViewSet):
    """
    ViewSet for authentication operations
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    @action(detail=False, methods=['post'])
    def register(self, request):
        """Register a new user"""
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            create_audit_log(user, 'create', 'user', user.id, request=request)
            
            return Response({
                'message': 'Registration successful',
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def login(self, request):
        """Login user"""
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Check if 2FA is enabled
            if user.two_fa_enabled:
                # Store user ID in session for 2FA verification
                request.session['pending_2fa_user_id'] = user.id
                create_audit_log(user, 'login', 'user', user.id, 
                               {'status': 'pending_2fa'}, request)
                return Response({
                    'message': '2FA verification required',
                    'requires_2fa': True
                }, status=status.HTTP_200_OK)
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            user.last_login = timezone.now()
            user.last_login_ip = get_client_ip(request)
            user.save(update_fields=['last_login', 'last_login_ip'])
            
            create_audit_log(user, 'login', 'user', user.id, request=request)
            
            return Response({
                'message': 'Login successful',
                'user': UserSerializer(user).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def logout(self, request):
        """Logout user"""
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            create_audit_log(request.user, 'logout', 'user', request.user.id, request=request)
            
            return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def verify_2fa(self, request):
        """Verify 2FA token"""
        serializer = TwoFactorVerifySerializer(data=request.data)
        if serializer.is_valid():
            user_id = request.session.get('pending_2fa_user_id')
            if not user_id:
                return Response({'error': '2FA session expired'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, 
                              status=status.HTTP_404_NOT_FOUND)
            
            token = serializer.validated_data['token']
            if user.verify_2fa_token(token):
                # Clear session
                del request.session['pending_2fa_user_id']
                
                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                user.last_login = timezone.now()
                user.last_login_ip = get_client_ip(request)
                user.save(update_fields=['last_login', 'last_login_ip'])
                
                create_audit_log(user, 'login', 'user', user.id, 
                               {'status': '2fa_verified'}, request)
                
                return Response({
                    'message': 'Login successful',
                    'user': UserSerializer(user).data,
                    'tokens': {
                        'access': str(refresh.access_token),
                        'refresh': str(refresh),
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid 2FA token'}, 
                              status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User management
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['list', 'create', 'destroy']:
            return [IsAdmin()]
        elif self.action in ['update', 'partial_update']:
            return [IsOwnerOrAdmin()]
        return super().get_permissions()

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user profile"""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put'])
    def update_profile(self, request):
        """Update current user profile"""
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            create_audit_log(request.user, 'update', 'user', request.user.id, 
                           request.data, request)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Change user password"""
        serializer = PasswordChangeSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data['old_password']):
                return Response({'error': 'Invalid old password'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            create_audit_log(user, 'update', 'user', user.id, 
                           {'action': 'password_change'}, request)
            
            return Response({'message': 'Password changed successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def setup_2fa(self, request):
        """Setup or disable 2FA"""
        serializer = TwoFactorSetupSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            enable = serializer.validated_data['enable']
            
            if enable:
                # Generate secret and return QR code
                user.generate_2fa_secret()
                qr_code = user.get_2fa_qr_code()
                
                return Response({
                    'message': '2FA setup initiated',
                    'qr_code': qr_code,
                    'secret': user.two_fa_secret,
                    'manual_entry_key': user.two_fa_secret
                })
            else:
                # Disable 2FA
                user.two_fa_enabled = False
                user.two_fa_secret = None
                user.save()
                
                create_audit_log(user, 'update', 'user', user.id, 
                               {'action': '2fa_disabled'}, request)
                
                return Response({'message': '2FA disabled successfully'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def confirm_2fa(self, request):
        """Confirm 2FA setup with verification token"""
        serializer = TwoFactorVerifySerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            token = serializer.validated_data['token']
            
            if user.verify_2fa_token(token):
                user.two_fa_enabled = True
                user.save()
                
                create_audit_log(user, 'update', 'user', user.id, 
                               {'action': '2fa_enabled'}, request)
                
                return Response({'message': '2FA enabled successfully'})
            else:
                return Response({'error': 'Invalid 2FA token'}, 
                              status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PhotographerProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Photographer Profile management
    """
    queryset = PhotographerProfile.objects.all()
    serializer_class = PhotographerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return self.queryset
        return self.queryset.filter(user=user)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Audit Log (read-only)
    """
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdmin]
    
    def get_queryset(self):
        queryset = self.queryset
        user_id = self.request.query_params.get('user_id')
        action = self.request.query_params.get('action')
        target_type = self.request.query_params.get('target_type')
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if action:
            queryset = queryset.filter(action=action)
        if target_type:
            queryset = queryset.filter(target_type=target_type)
        
        return queryset
