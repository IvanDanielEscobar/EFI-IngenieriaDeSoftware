from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Q, Value, IntegerField
from django.db.models.functions import Coalesce

from .models import Categoria, Material, Mueble, Pedido
from .serializers import (
    CategoriaSerializer,
    MaterialSerializer,
    MuebleSerializer,
    MuebleListSerializer,
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
        # Nested serializer para list (get all) y para destacados
        if self.action in ['list', 'destacados']:
            return MuebleListSerializer
        return MuebleSerializer

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