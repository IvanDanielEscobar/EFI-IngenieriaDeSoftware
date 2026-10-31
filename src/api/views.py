from rest_framework import viewsets, filters
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
from .pagination import MueblePagination, StandardResultsSetPagination

class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'descripcion']
    ordering = ['nombre']


class MaterialViewSet(viewsets.ModelViewSet):
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'descripcion']
    ordering = ['nombre']


class MuebleViewSet(viewsets.ModelViewSet):
    pagination_class = MueblePagination
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

class SucursalViewSet(viewsets.ModelViewSet):
    """
    CRUD para la gestion de sucursales.
    Busqueda por nombre, ciudad, provincia y dirección.
    """
    queryset = Sucursal.objects.all()
    serializer_class = SucursalSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'ciudad', 'direccion', 'provincia', 'telefono']
    ordering_fields = ['nombre', 'ciudad']
    ordering = ['nombre']


class MetodoPagoViewSet(viewsets.ModelViewSet):
    """
    CRUD para la gestion de metodos de pago.
    Busqueda por nombre y tipo.
    """
    queryset = MetodoPago.objects.all()
    serializer_class = MetodoPagoSerializer
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
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['mueble__nombre', 'color']
    ordering_fields = ['precio', 'stock', 'alto', 'ancho', 'profundidad']
    ordering = ['precio']
