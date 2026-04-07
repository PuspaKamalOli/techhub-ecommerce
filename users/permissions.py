from rest_framework import permissions

class IsAdminRole(permissions.BasePermission):
    """
    Allows access only to users with the 'admin' role.
    """
    def hasattr_profile(self, user):
        return hasattr(user, 'profile')

    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            self.hasattr_profile(request.user) and 
            request.user.profile.role == 'admin'
        )

class IsManagerRole(permissions.BasePermission):
    """
    Allows access only to users with the 'manager' or 'admin' role.
    """
    def hasattr_profile(self, user):
        return hasattr(user, 'profile')

    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            self.hasattr_profile(request.user) and 
            request.user.profile.role in ['manager', 'admin']
        )

class IsCustomerRole(permissions.BasePermission):
    """
    Allows access to properly authenticated customers.
    """
    def hasattr_profile(self, user):
        return hasattr(user, 'profile')

    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            self.hasattr_profile(request.user) and 
            request.user.profile.role == 'customer'
        )
