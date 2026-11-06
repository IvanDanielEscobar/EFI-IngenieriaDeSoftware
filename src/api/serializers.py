from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken
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
            'imagen',
            'fecha_creacion',
            'fecha_actualizacion',
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']


# Nested serializer para list (get all) y para destacados
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
    usuario = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.all(),
        required=False,
        allow_null=True
    )
    usuario_username = serializers.ReadOnlyField(source='usuario.username')
    usuario_email = serializers.ReadOnlyField(source='usuario.email')
    usuario_nombre_completo = serializers.SerializerMethodField()

    # Campos opcionales para crear usuario nuevo directamente al registrar un cliente
    username = serializers.CharField(write_only=True, required=False)
    email = serializers.EmailField(write_only=True, required=False)
    password = serializers.CharField(write_only=True, required=False, style={'input_type': 'password'})
    first_name = serializers.CharField(write_only=True, required=False, default='')
    last_name = serializers.CharField(write_only=True, required=False, default='')

    class Meta:
        model = Cliente
        fields = [
            'id',
            'usuario',
            'username',
            'email',
            'password',
            'first_name',
            'last_name',
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

    @extend_schema_field(serializers.CharField)
    def get_usuario_nombre_completo(self, obj) -> str:
        return obj.usuario.get_full_name() or obj.usuario.username

    def validate(self, attrs):
        usuario = attrs.get('usuario')
        username = attrs.get('username')
        password = attrs.get('password')

        # Si se crea un cliente nuevo (sin usuario preexistente)
        if not self.instance:
            if not usuario and not username:
                raise serializers.ValidationError(
                    "Debe indicar un 'usuario' existente o proporcionar 'username' y 'password' para dar de alta al cliente."
                )
            if username:
                if not password:
                    raise serializers.ValidationError({"password": "Debe proporcionar una contraseña para el nuevo usuario."})
                if Usuario.objects.filter(username__iexact=username).exists():
                    raise serializers.ValidationError({"username": "El nombre de usuario ya está registrado."})
                email = attrs.get('email')
                if email and Usuario.objects.filter(email__iexact=email).exists():
                    raise serializers.ValidationError({"email": "El correo electrónico ya está registrado."})

        return attrs

    def create(self, validated_data):
        username = validated_data.pop('username', None)
        email = validated_data.pop('email', '')
        password = validated_data.pop('password', None)
        first_name = validated_data.pop('first_name', '')
        last_name = validated_data.pop('last_name', '')

        if username and password:
            usuario = Usuario.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                rol=Usuario.Rol.CLIENTE
            )
            validated_data['usuario'] = usuario

        return super().create(validated_data)


# Serializadores de Registro y Gestión de Usuarios

class RegistroClienteSerializer(serializers.ModelSerializer):
    """
    Serializador para el registro público de nuevos clientes desde la tienda web / frontend.
    Crea el Usuario con rol CLIENTE y su perfil Cliente en una sola transacción atómica.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    dni_cuit = serializers.CharField(write_only=True, required=True, max_length=20)
    telefono = serializers.CharField(write_only=True, required=False, allow_blank=True, default='')
    direccion = serializers.CharField(write_only=True, required=False, allow_blank=True, default='')
    es_mayorista = serializers.BooleanField(write_only=True, required=False, default=False)

    cliente_id = serializers.SerializerMethodField(read_only=True)
    tokens = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Usuario
        fields = [
            'id',
            'username',
            'email',
            'password',
            'first_name',
            'last_name',
            'dni_cuit',
            'telefono',
            'direccion',
            'es_mayorista',
            'cliente_id',
            'tokens',
        ]
        extra_kwargs = {
            'email': {'required': True},
        }

    def validate_username(self, value):
        if Usuario.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("El nombre de usuario ya se encuentra registrado.")
        return value

    def validate_email(self, value):
        if Usuario.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("El correo electrónico ya se encuentra registrado.")
        return value

    def validate_dni_cuit(self, value):
        if Cliente.objects.filter(dni_cuit=value).exists():
            raise serializers.ValidationError("El DNI/CUIT ya se encuentra registrado.")
        return value

    def create(self, validated_data):
        dni_cuit = validated_data.pop('dni_cuit')
        telefono = validated_data.pop('telefono', '')
        direccion = validated_data.pop('direccion', '')
        es_mayorista = validated_data.pop('es_mayorista', False)
        password = validated_data.pop('password')

        usuario = Usuario.objects.create_user(
            rol=Usuario.Rol.CLIENTE,
            password=password,
            **validated_data
        )

        Cliente.objects.create(
            usuario=usuario,
            dni_cuit=dni_cuit,
            telefono=telefono,
            direccion=direccion,
            es_mayorista=es_mayorista,
        )

        return usuario

    @extend_schema_field(serializers.IntegerField)
    def get_cliente_id(self, obj):
        return getattr(obj, 'perfil_cliente', None).id if hasattr(obj, 'perfil_cliente') else None

    @extend_schema_field(serializers.DictField)
    def get_tokens(self, obj):
        refresh = RefreshToken.for_user(obj)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }


class UsuarioSerializer(serializers.ModelSerializer):
    """
    Serializador completo para administración de usuarios (Superadmin y Administrador).
    Permite asignar roles (ADMIN, EMPLEADO, CLIENTE), dar de alta y editar perfiles.
    """
    cliente = serializers.SerializerMethodField(read_only=True)
    password = serializers.CharField(write_only=True, required=False, validators=[validate_password])

    # Campos opcionales para clientes
    dni_cuit = serializers.CharField(write_only=True, required=False, max_length=20)
    telefono = serializers.CharField(write_only=True, required=False, allow_blank=True)
    direccion = serializers.CharField(write_only=True, required=False, allow_blank=True)
    es_mayorista = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = Usuario
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'rol',
            'is_active',
            'is_staff',
            'is_superuser',
            'date_joined',
            'password',
            'dni_cuit',
            'telefono',
            'direccion',
            'es_mayorista',
            'cliente',
        ]
        read_only_fields = ['id', 'date_joined']

    @extend_schema_field(serializers.DictField)
    def get_cliente(self, obj):
        perfil = getattr(obj, 'perfil_cliente', None)
        if perfil:
            return {
                'id': perfil.id,
                'dni_cuit': perfil.dni_cuit,
                'telefono': perfil.telefono,
                'direccion': perfil.direccion,
                'es_mayorista': perfil.es_mayorista,
            }
        return None

    def validate(self, attrs):
        request = self.context.get('request')
        target_superuser = attrs.get('is_superuser')

        # Restricción: Solo un superusuario puede otorgar is_superuser=True
        if target_superuser and not (request and request.user.is_superuser):
            raise serializers.ValidationError({"is_superuser": "Solo un superadministrador puede otorgar privilegios de superusuario."})

        # Restricción: Un administrador normal no puede modificar ni revocar a un superusuario
        if self.instance and self.instance.is_superuser and not (request and request.user.is_superuser):
            raise serializers.ValidationError("No tienes permiso para modificar a un superadministrador.")

        return attrs

    def create(self, validated_data):
        dni_cuit = validated_data.pop('dni_cuit', None)
        telefono = validated_data.pop('telefono', '')
        direccion = validated_data.pop('direccion', '')
        es_mayorista = validated_data.pop('es_mayorista', False)
        password = validated_data.pop('password', None)

        rol = validated_data.get('rol', Usuario.Rol.CLIENTE)
        if rol in [Usuario.Rol.ADMIN, Usuario.Rol.EMPLEADO]:
            validated_data['is_staff'] = True

        if password:
            usuario = Usuario.objects.create_user(password=password, **validated_data)
        else:
            usuario = Usuario.objects.create(**validated_data)

        if rol == Usuario.Rol.CLIENTE and dni_cuit:
            Cliente.objects.create(
                usuario=usuario,
                dni_cuit=dni_cuit,
                telefono=telefono,
                direccion=direccion,
                es_mayorista=es_mayorista,
            )

        return usuario

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        dni_cuit = validated_data.pop('dni_cuit', None)
        telefono = validated_data.pop('telefono', None)
        direccion = validated_data.pop('direccion', None)
        es_mayorista = validated_data.pop('es_mayorista', None)

        if password:
            instance.set_password(password)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if instance.rol in [Usuario.Rol.ADMIN, Usuario.Rol.EMPLEADO]:
            instance.is_staff = True

        instance.save()

        # Actualizar perfil de cliente si corresponde
        if hasattr(instance, 'perfil_cliente'):
            cliente = instance.perfil_cliente
            if dni_cuit is not None:
                cliente.dni_cuit = dni_cuit
            if telefono is not None:
                cliente.telefono = telefono
            if direccion is not None:
                cliente.direccion = direccion
            if es_mayorista is not None:
                cliente.es_mayorista = es_mayorista
            cliente.save()
        elif instance.rol == Usuario.Rol.CLIENTE and dni_cuit:
            Cliente.objects.create(
                usuario=instance,
                dni_cuit=dni_cuit,
                telefono=telefono or '',
                direccion=direccion or '',
                es_mayorista=bool(es_mayorista),
            )

        return instance


# Serializadores de Pedidos y Detalles

class DetallePedidoSerializer(serializers.ModelSerializer):
    mueble_nombre = serializers.ReadOnlyField(source='mueble.nombre')
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = DetallePedido
        fields = [
            'id',
            'pedido',
            'mueble',
            'mueble_nombre',
            'cantidad',
            'precio_unitario',
            'subtotal',
        ]
        read_only_fields = ['id', 'precio_unitario']


class DetallePedidoListSerializer(serializers.ModelSerializer):
    mueble = MuebleSerializer(read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = DetallePedido
        fields = [
            'id',
            'mueble',
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


class PedidoListSerializer(serializers.ModelSerializer):
    cliente = ClienteSerializer(read_only=True)
    sucursal = SucursalSerializer(read_only=True)
    metodo_pago = MetodoPagoSerializer(read_only=True)
    detalles = DetallePedidoListSerializer(many=True, read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = Pedido
        fields = [
            'id',
            'numero_pedido',
            'cliente',
            'sucursal',
            'metodo_pago',
            'estado',
            'estado_display',
            'direccion_entrega',
            'total',
            'notas',
            'detalles',
            'fecha_creacion',
            'fecha_actualizacion',
        ]
