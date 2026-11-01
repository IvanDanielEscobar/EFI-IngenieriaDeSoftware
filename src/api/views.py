from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .models import Categoria, Material, Mueble, Pedido
from .serializers import (
    CategoriaSerializer,
    MaterialSerializer,
    MuebleSerializer,
    MuebleListSerializer,
    PedidoSerializer
)
from .pagination import MueblePagination

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