from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
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
)


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'descripcion']


class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = ['id', 'nombre', 'descripcion']


class CaracteristicasSerializer(serializers.ModelSerializer):
    en_stock = serializers.BooleanField(read_only=True)
    dimensiones_texto = serializers.CharField(read_only=True)
    mueble_nombre = serializers.ReadOnlyField(source='mueble.nombre')

    class Meta:
        model = Caracteristicas
        fields = [
            'id',
            'mueble',
            'mueble_nombre',
            'alto',
            'ancho',
            'profundidad',
            'peso',
            'precio',
            'stock',
            'color',
            'en_stock',
            'dimensiones_texto',
        ]


# Serializador CRUD estándar (recibe IDs para categoria y material)
class MuebleSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.ReadOnlyField(source='categoria.nombre')
    material_nombre = serializers.ReadOnlyField(source='material.nombre')

    class Meta:
        model = Mueble
        fields = [
            'id',
            'nombre',
            'descripcion',
            'categoria',
            'categoria_nombre',
            'material',
            'material_nombre',
            'fecha_creacion',
            'fecha_actualizacion',
            'imagen',
        ]


# Nested Serializer exclusivo para la acción 'list' (get all)
class MuebleListSerializer(serializers.ModelSerializer):
    categoria = CategoriaSerializer(read_only=True)
    material = MaterialSerializer(read_only=True)
    caracteristicas = CaracteristicasSerializer(read_only=True)
    total_vendido = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Mueble
        fields = [
            'id',
            'nombre',
            'descripcion',
            'categoria',
            'material',
            'imagen',
            'total_vendido',
            'caracteristicas',
            'fecha_creacion',
            'fecha_actualizacion',
        ]

class DetallePedidoSerializer(serializers.ModelSerializer):
    mueble_nombre = serializers.ReadOnlyField(source='mueble.nombre')
    subtotal = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = DetallePedido
        fields = [
            'id',
            'mueble',
            'mueble_nombre',
            'cantidad',
            'precio_unitario',
            'subtotal',
        ]


class PedidoSerializer(serializers.ModelSerializer):
    cliente_username = serializers.ReadOnlyField(source='cliente.usuario.username')
    sucursal_nombre = serializers.ReadOnlyField(source='sucursal.nombre')
    metodo_pago_nombre = serializers.ReadOnlyField(source='metodo_pago.nombre')
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    detalles = DetallePedidoSerializer(many=True, read_only=True)

    class Meta:
        model = Pedido
        fields = [
            'id',
            'numero_pedido',
            'cliente',
            'cliente_username',
            'sucursal',
            'sucursal_nombre',
            'metodo_pago',
            'metodo_pago_nombre',
            'estado',
            'estado_display',
            'direccion_entrega',
            'total',
            'notas',
            'detalles',
            'fecha_creacion',
            'fecha_actualizacion',
        ]
        read_only_fields = [
            'id',
            'numero_pedido',
            'estado',
            'total',
            'fecha_creacion',
            'fecha_actualizacion',
        ]
# Serializadores de Soporte

class SucursalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sucursal
        fields = [
            'id',
            'nombre',
            'direccion',
            'ciudad',
            'provincia',
            'telefono',
            'email',
            'activa',
        ]


class MetodoPagoSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = MetodoPago
        fields = [
            'id',
            'nombre',
            'tipo',
            'tipo_display',
            'activo',
            'instrucciones',
        ]


class ClienteSerializer(serializers.ModelSerializer):
    usuario_username = serializers.ReadOnlyField(source='usuario.username')
    usuario_email = serializers.ReadOnlyField(source='usuario.email')
    usuario_nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = Cliente
        fields = [
            'id',
            'usuario',
            'usuario_username',
            'usuario_email',
            'usuario_nombre_completo',
            'telefono',
            'direccion',
            'dni_cuit',
            'es_mayorista',
            'fecha_creacion',
        ]
        read_only_fields = ['id', 'fecha_creacion']

    def get_usuario_nombre_completo(self, obj):
        return obj.usuario.get_full_name() or obj.usuario.username
