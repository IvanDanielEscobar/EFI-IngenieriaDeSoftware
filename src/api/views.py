from rest_framework import viewsets, filters
from rest_framework.exceptions import PermissionDenied
from .models import (
    Categoria,
    Material,
    Mueble,
    Caracteristicas,
    Cliente,
    Sucursal,
    MetodoPago,
)
from .serializers import (
    CategoriaSerializer,
    MaterialSerializer,
    MuebleSerializer,
    MuebleListSerializer,
    CaracteristicasSerializer,
    SucursalSerializer,
    MetodoPagoSerializer,
    ClienteSerializer,
)
from .permissions import IsEmpleadoOrPublicReadOnly, IsEmpleado
from .pagination import MueblePagination, StandardResultsSetPagination


class EliminadoLogicoDestroyMixin:
    """
    Control de borrado para modelos con baja lógica:
    - Borrado estándar (DELETE): realiza baja lógica (instance.delete()), permitido a administradores.
    - Borrado definitivo (DELETE con ?hard=true): eliminación física (instance.borrado_fisico()),
      exclusivo para superadministradores (is_superuser).
    """
    def perform_destroy(self, instance):
        hard_delete = self.request.query_params.get('hard', '').lower() in ('true', '1')
        if hard_delete:
            if not self.request.user.is_superuser:
                raise PermissionDenied("La eliminación definitiva está restringida únicamente a superadministradores.")
            if hasattr(instance, 'borrado_fisico'):
                instance.borrado_fisico()
            else:
                instance.delete()
        else:
            instance.delete()


class CategoriaViewSet(EliminadoLogicoDestroyMixin, viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [IsEmpleadoOrPublicReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'descripcion']
    ordering = ['nombre']


class MaterialViewSet(EliminadoLogicoDestroyMixin, viewsets.ModelViewSet):
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer
    permission_classes = [IsEmpleadoOrPublicReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'descripcion']
    ordering = ['nombre']


class MuebleViewSet(EliminadoLogicoDestroyMixin, viewsets.ModelViewSet):
    pagination_class = MueblePagination
    permission_classes = [IsEmpleadoOrPublicReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'nombre',
        'descripcion',
        'categoria__nombre',
        'material__nombre',
        'caracteristicas__color',
    ]
    ordering_fields = ['nombre', 'fecha_creacion', 'caracteristicas__precio', 'caracteristicas__stock']
    ordering = ['-fecha_creacion']

    def get_queryset(self):
        # Mueble.objects ya excluye automáticamente los que tengan eliminado_logico=True
        queryset = Mueble.objects.all().select_related('categoria', 'material').prefetch_related('caracteristicas')
        
        # 1. Filtro por categoría (acepta ID o nombre)
        categoria = self.request.query_params.get('categoria')
        if categoria:
            if categoria.isdigit():
                queryset = queryset.filter(categoria_id=int(categoria))
            else:
                queryset = queryset.filter(categoria__nombre__icontains=categoria)
        
        # 2. Filtro por rango de precios
        precio_min = self.request.query_params.get('precio_min')
        if precio_min:
            queryset = queryset.filter(caracteristicas__precio__gte=precio_min)
        
        precio_max = self.request.query_params.get('precio_max')
        if precio_max:
            queryset = queryset.filter(caracteristicas__precio__lte=precio_max)
        
        return queryset
    
    def get_serializer_class(self):
        # Nested serializer exclusivo para list (get all)
        if self.action == 'list':
            return MuebleListSerializer
        return MuebleSerializer


# ViewSets de Soporte

class SucursalViewSet(EliminadoLogicoDestroyMixin, viewsets.ModelViewSet):
    """
    CRUD para la gestion de sucursales.
    Busqueda por nombre, ciudad, provincia y dirección.
    """
    queryset = Sucursal.objects.all()
    serializer_class = SucursalSerializer
    permission_classes = [IsEmpleadoOrPublicReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'ciudad', 'direccion', 'provincia', 'telefono']
    ordering_fields = ['nombre', 'ciudad']
    ordering = ['nombre']


class MetodoPagoViewSet(EliminadoLogicoDestroyMixin, viewsets.ModelViewSet):
    """
    CRUD para la gestion de metodos de pago.
    Busqueda por nombre y tipo.
    """
    queryset = MetodoPago.objects.all()
    serializer_class = MetodoPagoSerializer
    permission_classes = [IsEmpleadoOrPublicReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'tipo']
    ordering_fields = ['nombre', 'tipo']
    ordering = ['nombre']


class ClienteViewSet(viewsets.ModelViewSet):
    """
    CRUD para la administracion de clientes.
    Optimiza la consulta de usuario con select_related y permite busquedas por dni, telefono o usuario.
    """
    queryset = Cliente.objects.all().select_related('usuario')
    serializer_class = ClienteSerializer
    permission_classes = [IsEmpleado]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'usuario__username',
        'usuario__email',
        'usuario__first_name',
        'usuario__last_name',
        'dni_cuit',
        'telefono',
        'direccion',
    ]
    ordering_fields = ['fecha_creacion', 'usuario__username', 'dni_cuit']
    ordering = ['-fecha_creacion']


class CaracteristicasViewSet(viewsets.ModelViewSet):
    """
    CRUD para las caracteristicas tecnicas, precio y stock de muebles.
    Optimiza la relacion del mueble y permite ordenarlos por precio y stock.
    """
    queryset = Caracteristicas.objects.all().select_related('mueble')
    serializer_class = CaracteristicasSerializer
    permission_classes = [IsEmpleadoOrPublicReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['mueble__nombre', 'color']
    ordering_fields = ['precio', 'stock', 'alto', 'ancho', 'profundidad']
    ordering = ['precio']
