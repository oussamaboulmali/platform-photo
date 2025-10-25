"""
Serializers for User authentication
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, PhotographerProfile, AuditLog


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'role', 'phone', 'bio', 'profile_image', 'is_verified',
            'two_fa_enabled', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_verified']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'email', 'username', 'first_name', 'last_name',
            'password', 'password_confirm', 'role', 'phone'
        ]

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        # Customers can self-register, others need admin approval
        role = validated_data.get('role', 'customer')
        if role != 'customer':
            validated_data['is_active'] = False
        
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        
        # Create photographer profile if applicable
        if role in ['photographer', 'infographiste']:
            PhotographerProfile.objects.create(
                user=user,
                display_name=f"{user.first_name} {user.last_name}"
            )
        
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for login"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError("Invalid credentials")
            if not user.is_active:
                raise serializers.ValidationError("Account is disabled")
            data['user'] = user
        else:
            raise serializers.ValidationError("Must include email and password")
        
        return data


class TwoFactorSetupSerializer(serializers.Serializer):
    """Serializer for 2FA setup"""
    enable = serializers.BooleanField()


class TwoFactorVerifySerializer(serializers.Serializer):
    """Serializer for 2FA verification"""
    token = serializers.CharField(max_length=6, min_length=6)


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change"""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError("New passwords do not match")
        return data


class PhotographerProfileSerializer(serializers.ModelSerializer):
    """Serializer for Photographer Profile"""
    user = UserSerializer(read_only=True)

    class Meta:
        model = PhotographerProfile
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'total_uploads', 
                           'total_approved', 'total_rejected', 'total_downloads']


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for Audit Log"""
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = AuditLog
        fields = '__all__'
        read_only_fields = ['id', 'created_at']
