from rest_framework import permissions
from .models import Usuario


class PermisoCatalogo(permissions.BasePermission):
    def has_permission(self, request, view):
        # 1. Consulta pública
        if request.method in permissions.SAFE_METHODS:
            return True

        # Para cualquier método de escritura se requiere autenticación
        if not request.user or not request.user.is_authenticated:
            return False

        # 2. Creación y modificación: rol EMPLEADO o Admin
        if request.method in ['POST', 'PUT', 'PATCH']:
            return (
                request.user.rol == Usuario.Rol.EMPLEADO
                or request.user.is_staff
                or request.user.is_superuser
            )

        # 3. Borrado (baja lógica): Solo Administrador / Staff
        if request.method == 'DELETE':
            return request.user.is_staff or request.user.is_superuser

        return False


class SoloSuperadmin(permissions.BasePermission):
    """Permite acceso exclusivamente al Superadministrador."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)