from rest_framework import serializers
from .models import Categoria, Material, Mueble, Caracteristicas, Pedido, DetallePedido


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'descripcion']


class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = ['id', 'nombre', 'descripcion']


class CaracteristicasSerializer(serializers.ModelSerializer):
    en_stock = serializers.ReadOnlyField()
    dimensiones_texto = serializers.ReadOnlyField()

    class Meta:
        model = Caracteristicas
        fields = [
            'id',
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

    class Meta:
        model = Mueble
        fields = [
            'id',
            'nombre',
            'descripcion',
            'categoria',
            'material',
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