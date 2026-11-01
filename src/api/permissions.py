from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsEmpleadoOrPublicReadOnly(BasePermission):
    """
    Politica de acceso para el catálogo y recursos de consulta:
    - Lectura (GET, HEAD, OPTIONS): Pública para cualquier visitante o usuario.
    - Creación y edición (POST, PUT, PATCH): Exclusiva para usuarios autenticados con rol Empleado (o Admin).
    - Borrado (DELETE): Restringido a usuarios Administradores (is_staff o is_superuser).
    """
    message = "No tienes permiso para realizar esta acción en el catálogo."

    def has_permission(self, request, view):
        # 1. Lectura libre para cualquier usuario (público)
        if request.method in SAFE_METHODS:
            return True

        # Para cualquier método de mutación se requiere estar autenticado
        if not (request.user and request.user.is_authenticated):
            return False

        # 2. Borrado reservado para administradores
        if request.method == 'DELETE':
            return bool(request.user.is_staff or request.user.is_superuser)

        # 3. Creación y edición (POST, PUT, PATCH) exclusivo para empleados
        return bool(request.user.es_empleado())


class IsEmpleado(BasePermission):
    """
    Permite acceso únicamente a usuarios autenticados con rol de EMPLEADO
    o administradores/superusuarios.
    """
    message = "Acceso restringido: Se requieren permisos de empleado o administrador."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.es_empleado()
        )


class IsMayorista(BasePermission):
    """
    Permite acceso a usuarios autenticados que sean clientes mayoristas,
    o bien empleados/superusuarios del sistema.
    """
    message = "Acceso restringido: Se requiere condición de cliente mayorista o empleado."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.es_empleado():
            return True
        perfil = getattr(request.user, 'perfil_cliente', None)
        return bool(perfil and perfil.es_mayorista)
