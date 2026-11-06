from rest_framework import viewsets, filters, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema
from django.db.models import Sum, Q, Value, IntegerField
from django.db.models.functions import Coalesce

from .models import (
    Usuario,
    Categoria,
    Material,
    Mueble,
    Caracteristicas,
    Cliente,
    Sucursal,
    MetodoPago,
    Pedido,
    DetallePedido,
)
from .serializers import (
    UsuarioSerializer,
    RegistroClienteSerializer,
    CategoriaSerializer,
    MaterialSerializer,
    MuebleSerializer,
    MuebleListSerializer,
    CaracteristicasSerializer,
    SucursalSerializer,
    MetodoPagoSerializer,
    ClienteSerializer,
    PedidoSerializer,
    PedidoListSerializer,
    DetallePedidoSerializer,
    DetallePedidoListSerializer,
)
from .permissions import IsEmpleadoOrPublicReadOnly, IsEmpleado, IsAdmin, SoloSuperadmin
from .pagination import StandardResultsSetPagination


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

    # Acción de borrado físico restringida exclusivamente a superadmin
    @action(detail=True, methods=['delete'], url_path='borrado-fisico', permission_classes=[SoloSuperadmin])
    def borrado_fisico_endpoint(self, request, pk=None):
        categoria = Categoria.todos_los_objetos.get(pk=pk)
        categoria.borrado_fisico()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MaterialViewSet(EliminadoLogicoDestroyMixin, viewsets.ModelViewSet):
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer
    permission_classes = [IsEmpleadoOrPublicReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'descripcion']
    ordering = ['nombre']


class MuebleViewSet(EliminadoLogicoDestroyMixin, viewsets.ModelViewSet):
    pagination_class = StandardResultsSetPagination
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
        # Nested serializer para list (get all) y para destacados
        if self.action in ['list', 'destacados']:
            return MuebleListSerializer
        return MuebleSerializer

    
    @action(detail=False, methods=['get'], url_path='destacados')
    def destacados(self, request):
        """
        Retorna los muebles más vendidos en base a pedidos válidos (no cancelados ni eliminados lógicamente).
        """
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
        # Fallback: si aún no se registraron ventas en la BD, mostrar los últimos publicados
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

class SucursalViewSet(EliminadoLogicoDestroyMixin, viewsets.ModelViewSet):
    """
    CRUD para la gestión de sucursales.
    Búsqueda por nombre, ciudad, provincia y dirección.
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
    CRUD para la gestión de métodos de pago.
    Búsqueda por nombre y tipo.
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
    CRUD para la administración de clientes.
    Acceso restringido a empleados.
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


class RegistroClienteView(APIView):
    """
    Endpoint público para que cualquier cliente se registre directamente desde la tienda web.
    Crea el usuario con rol CLIENTE y su perfil comercial, devolviendo los tokens JWT para login inmediato.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        request=RegistroClienteSerializer,
        responses={201: RegistroClienteSerializer},
        description="Registra un nuevo cliente con credenciales de usuario y perfil comercial, retornando tokens JWT."
    )
    def post(self, request, *args, **kwargs):
        serializer = RegistroClienteSerializer(data=request.data)
        if serializer.is_valid():
            usuario = serializer.save()
            return Response(
                {
                    "mensaje": "Cliente registrado exitosamente.",
                    "usuario": {
                        "id": usuario.id,
                        "username": usuario.username,
                        "email": usuario.email,
                        "rol": usuario.rol,
                        "cliente_id": getattr(usuario, 'perfil_cliente', None).id if hasattr(usuario, 'perfil_cliente') else None,
                    },
                    "tokens": serializer.get_tokens(usuario),
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UsuarioViewSet(viewsets.ModelViewSet):
    """
    Gestión administrativa de usuarios del sistema (Superadministradores y Administradores).
    Permite dar de alta usuarios y asignarles roles (ADMIN, EMPLEADO, CLIENTE).
    - Un Administrador solo puede realizar baja lógica/desactivación y no puede modificar superusuarios.
    - Incluye endpoint /api/usuarios/perfil/ para que el usuario autenticado consulte sus propios datos.
    """
    queryset = Usuario.objects.all().select_related('perfil_cliente').order_by('id')
    serializer_class = UsuarioSerializer
    permission_classes = [IsAdmin]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'username',
        'email',
        'first_name',
        'last_name',
        'rol',
        'perfil_cliente__dni_cuit',
    ]
    ordering_fields = ['id', 'username', 'email', 'rol', 'date_joined']
    ordering = ['id']

    @action(detail=False, methods=['get'], url_path='perfil', permission_classes=[IsAuthenticated])
    def perfil(self, request):
        """Devuelve los datos del usuario autenticado actual y su perfil comercial si existe."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    def perform_destroy(self, instance):
        if instance.is_superuser and not self.request.user.is_superuser:
            raise PermissionDenied("Solo un superadministrador puede desactivar a otro superadministrador.")
        # Baja lógica: desactiva el acceso en lugar de borrar registros históricos
        instance.is_active = False
        instance.save(update_fields=['is_active'])


class CaracteristicasViewSet(viewsets.ModelViewSet):
    """
    CRUD para las características técnicas, precio y stock de muebles.
    """
    queryset = Caracteristicas.objects.all().select_related('mueble')
    serializer_class = CaracteristicasSerializer
    permission_classes = [IsEmpleadoOrPublicReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['mueble__nombre', 'color']
    ordering_fields = ['precio', 'stock', 'alto', 'ancho', 'profundidad']
    ordering = ['precio']


# ViewSets de Transacciones y Pedidos

class PedidoViewSet(EliminadoLogicoDestroyMixin, viewsets.ModelViewSet):
    """
    CRUD y gestión operativa de Pedidos.
    - Seguridad: Sólo usuarios autenticados (IsAuthenticated).
    - get_queryset(): Empleados ven todos los pedidos; clientes sólo ven sus propios pedidos.
    """
    queryset = Pedido.objects.all()
    permission_classes = [IsAuthenticated]
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
        user = self.request.user
        queryset = Pedido.objects.all().select_related(
            'cliente__usuario',
            'sucursal',
            'metodo_pago',
        ).prefetch_related(
            'detalles__mueble__categoria',
            'detalles__mueble__material'
        )

        # Empleados y superusuarios ven la totalidad de los pedidos
        if user.is_authenticated and user.es_empleado():
            return queryset

        # Clientes regulares únicamente acceden a sus propios pedidos
        return queryset.filter(cliente__usuario=user)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return PedidoListSerializer
        return PedidoSerializer

    def perform_create(self, serializer):
        user = self.request.user
        if not user.es_empleado() and hasattr(user, 'perfil_cliente'):
            serializer.save(cliente=user.perfil_cliente)
        else:
            serializer.save()

    @action(detail=True, methods=['post'], url_path='cancelar')
    def cancelar(self, request, pk=None):
        """
        Cancela un pedido y realiza su baja lógica.
        Valida que el pedido pertenezca al usuario solicitante (o que sea empleado/admin)
        y que se encuentre dentro del plazo y estado cancelable.
        """
        try:
            pedido = Pedido.objects.get(pk=pk)
        except Pedido.DoesNotExist:
            return Response(
                {'detail': 'Pedido no encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Validación de pertenencia: Solo el dueño del pedido o un empleado/admin puede cancelar
        if not request.user.es_empleado() and pedido.cliente.usuario != request.user:
            return Response(
                {'detail': 'No tienes permiso para cancelar un pedido ajeno.'},
                status=status.HTTP_403_FORBIDDEN
            )

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


class DetallePedidoViewSet(viewsets.ModelViewSet):
    """
    CRUD para detalles individuales de pedidos.
    Restringido a usuarios autenticados, filtrado por pertenencia de pedido.
    """
    queryset = DetallePedido.objects.all()
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'pedido__numero_pedido',
        'mueble__nombre',
    ]

    def get_queryset(self):
        user = self.request.user
        queryset = DetallePedido.objects.all().select_related(
            'pedido',
            'mueble__categoria',
            'mueble__material'
        )

        if user.is_authenticated and user.es_empleado():
            return queryset

        return queryset.filter(pedido__cliente__usuario=user)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return DetallePedidoListSerializer
        return DetallePedidoSerializer
