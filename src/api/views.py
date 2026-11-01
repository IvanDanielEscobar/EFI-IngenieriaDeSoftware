from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, Q, Value, IntegerField
from django.db.models.functions import Coalesce

from .models import (
    Categoria,
    Material,
    Mueble,
    Caracteristicas,
    Cliente,
    Sucursal,
    MetodoPago,
    Pedido,
    DetallePedido,
    Pedido,
)
from .serializers import (
    CategoriaSerializer,
    MaterialSerializer,
    MuebleSerializer,
    MuebleListSerializer,
    PedidoSerializer
    CaracteristicasSerializer,
    SucursalSerializer,
    MetodoPagoSerializer,
    ClienteSerializer,
    PedidoSerializer,
    PedidoListSerializer,
    DetallePedidoSerializer,
    DetallePedidoListSerializer,
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
        # Nested serializer para list (get all) y para destacados
        if self.action in ['list', 'destacados']:
            return MuebleListSerializer
        return MuebleSerializer

class PedidoViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PedidoSerializer
    pagination_class = MueblePagination  # cambiar a StandardResultsSetPagination cuando se mergee la otra rama
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'numero_pedido',
        'cliente__usuario__username',
        'cliente__dni_cuit',
        'direccion_entrega',
    ]
    ordering_fields = ['numero_pedido', 'fecha_creacion', 'total', 'estado']
    ordering = ['-fecha_creacion']

    def get_queryset(self):
        # Pedido.objects excluye automáticamente los eliminados lógicamente (cancelados)
        return Pedido.objects.all().select_related(
            'cliente__usuario', 'sucursal', 'metodo_pago'
        ).prefetch_related('detalles__mueble')

    @action(detail=True, methods=['post'], url_path='cancelar')
    def cancelar(self, request, pk=None):
        pedido = self.get_object()
        if not pedido.puede_cancelarse():
            return Response(
                {'detail': 'El pedido no puede cancelarse (estado no válido o plazo de 24 horas vencido).'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        pedido.cancelar()
        return Response(
            {
                'detail': f'Pedido #{pedido.numero_pedido} cancelado correctamente.',
                'pedido': PedidoSerializer(pedido).data,
            },
            status=status.HTTP_200_OK,
        )
    @action(detail=False, methods=['get'], url_path='destacados')
    def destacados(self, request):
        # Anota cada mueble con la suma de cantidades vendidas en pedidos validos
        queryset = (
            self.get_queryset()
            .annotate(
                total_vendido=Coalesce(
                    Sum(
                        'detalles_pedido__cantidad',
                        filter=~Q(detalles_pedido__pedido__estado=Pedido.EstadoPedido.CANCELADO)
                        & Q(detalles_pedido__pedido__eliminado_logico=False),
                    ),
                    Value(0),
                    output_field=IntegerField(),
                )
            )
            .filter(total_vendido__gt=0)
            .order_by('-total_vendido', '-fecha_creacion')
        )
        # Fallback: si aun no se registraron ventas en la base de datos, mostrar los ultimos publicados
        if not queryset.exists():
            queryset = (
                self.get_queryset()
                .annotate(total_vendido=Value(0, output_field=IntegerField()))
                .order_by('-fecha_creacion')
            )
        limite = request.query_params.get('limite', 5)
        try:
            limite = max(1, int(limite))
        except ValueError:
            limite = 5
        muebles_destacados = queryset[:limite]
        serializer = self.get_serializer(muebles_destacados, many=True)
        return Response(serializer.data)

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

class PedidoViewSet(viewsets.ModelViewSet):
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'numero_pedido',
        'cliente__usuario__username',
        'cliente__dni_cuit',
        'direccion_entrega',
        'estado',
    ]
    ordering_fields = ['numero_pedido', 'fecha_creacion', 'total', 'estado']
    ordering = ['-fecha_creacion']

    def get_queryset(self):
        return Pedido.objects.all().select_related(
            'cliente__usuario',
            'sucursal',
            'metodo_pago',
        ).prefetch_related(
            'detalles__mueble_categoria',
            'detalles__mueble__material'
        )
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return PedidoListSerializer
        return PedidoSerializer

class DetallePedidoViewSet(viewsets.ModelViewSet):
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'pedido__numero_pedido',
        'mueble__nombre',
    ]

    def get_queryset(self):
        return DetallePedido.objects.all().select_related(
            'pedido',
            'mueble__categoria',
            'mueble__material'
        )

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return DetallePedidoListSerializer
        return DetallePedidoSerializer