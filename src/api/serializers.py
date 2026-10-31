from rest_framework import serializers
from .models import Categoria, Material, Mueble, Caracteristicas


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