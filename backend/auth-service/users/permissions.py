"""
Custom permissions for user authentication
"""
from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Permission check for admin role
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


class IsValidator(permissions.BasePermission):
    """
    Permission check for validator role
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['validator', 'admin']


class IsPhotographer(permissions.BasePermission):
    """
    Permission check for photographer role
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['photographer', 'admin']


class IsInfographiste(permissions.BasePermission):
    """
    Permission check for infographiste role
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['infographiste', 'admin']


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission check for resource owner or admin
    """
    def has_object_permission(self, request, view, obj):
        # Admin has full access
        if request.user.role == 'admin':
            return True
        
        # Check if obj has user attribute and matches request user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # For User objects
        if hasattr(obj, 'id'):
            return obj.id == request.user.id
        
        return False


class CanUpload(permissions.BasePermission):
    """
    Permission check for users who can upload content
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and \
               request.user.role in ['photographer', 'infographiste', 'admin']
