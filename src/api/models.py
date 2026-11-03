from decimal import Decimal
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import MinValueValidator

class Usuario(AbstractUser):
    class Rol(models.TextChoices):
        EMPLEADO= 'EMPLEADO', 'Empleado'
        CLIENTE = 'CLIENTE', 'Cliente'

    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.CLIENTE,
        help_text="Define el rol y permisos operativos del usuario en el sistema."
    )
    
    def es_empleado(self):
        return self.rol == self.Rol.EMPLEADO or self.is_superuser
    
    def __str__(self):
        return f"{self.username} ({self.get_rol_display()})"


class Cliente(models.Model):
    
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil_cliente'
    )

    telefono = models.CharField(max_length=30, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    dni_cuit = models.CharField(max_length=20, unique=True, verbose_name="DNI / CUIT")
    es_mayorista = models.BooleanField(
        default=False,
        help_text="Indica si el cliente accede a condiciones de compra mayorista."
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.usuario.get_full_name() or self.usuario.username} - {self.dni_cuit}"

# Clase Base y Managers para Eliminado Lógico

class EliminadoLogicoQuerySet(models.QuerySet):
    def delete(self):
        """Eliminado lógico en masa mediante QuerySet (ej. Model.objects.filter(...).delete())."""
        return self.update(eliminado_logico=True)

    def restaurar(self):
        """Restaura en masa registros eliminados lógicamente."""
        return self.update(eliminado_logico=False)


class EliminadoLogicoManager(models.Manager):
    def get_queryset(self):
        """Por defecto filtra y retorna únicamente los registros que NO fueron eliminados lógicamente."""
        return EliminadoLogicoQuerySet(self.model, using=self._db).filter(eliminado_logico=False)


class EliminadoLogicoModel(models.Model):
    eliminado_logico = models.BooleanField(
        default=False,
        verbose_name="Eliminado lógicamente",
        help_text="Indica si el registro fue dado de baja de forma lógica en el sistema."
    )

    objects = EliminadoLogicoManager()
    todos_los_objetos = models.Manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """Sobrescribe el borrado estándar para realizar baja lógica."""
        self.eliminado_logico = True
        self.save(update_fields=['eliminado_logico'])

    def restaurar(self):
        """Restaura un registro eliminado lógicamente."""
        self.eliminado_logico = False
        self.save(update_fields=['eliminado_logico'])

    def borrado_fisico(self, using=None, keep_parents=False):
        """Elimina permanentemente el registro de la base de datos (hard delete)."""
        super().delete(using=using, keep_parents=keep_parents)


# Modelos del Catálogo de Mueblería

class Categoria(EliminadoLogicoModel):
    nombre = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nombre"
    )
    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción"
    )

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Material(EliminadoLogicoModel):
    nombre = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nombre del material"
    )
    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción"
    )

    class Meta:
        verbose_name = "Material"
        verbose_name_plural = "Materiales"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Mueble(EliminadoLogicoModel):
    nombre = models.CharField(
        max_length=150,
        verbose_name="Nombre del mueble"
    )
    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción general"
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name='muebles',
        verbose_name="Categoría"
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        related_name='muebles',
        verbose_name="Material"
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de actualización"
    )
    imagen = models.ImageField(
        upload_to="media/",
        null=True,
        blank=True,
        verbose_name="Imagen del mueble"
    )

    class Meta:
        verbose_name = "Mueble"
        verbose_name_plural = "Muebles"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.nombre} ({self.categoria.nombre})"


class Caracteristicas(models.Model):
    mueble = models.OneToOneField(
        Mueble,
        on_delete=models.CASCADE,
        related_name='caracteristicas',
        verbose_name="Mueble"
    )
    alto = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Alto en centímetros (cm)",
        verbose_name="Alto (cm)"
    )
    ancho = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Ancho en centímetros (cm)",
        verbose_name="Ancho (cm)"
    )
    profundidad = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Profundidad en centímetros (cm)",
        verbose_name="Profundidad (cm)"
    )
    peso = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Peso en kilogramos (kg)",
        verbose_name="Peso (kg)"
    )
    precio = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Precio unitario en ARS",
        verbose_name="Precio"
    )
    stock = models.PositiveIntegerField(
        default=0,
        help_text="Unidades físicas disponibles en depósito",
        verbose_name="Stock disponible"
    )
    color = models.CharField(
        max_length=60,
        blank=True,
        null=True,
        help_text="Color o acabado (ej. Nogal, Laqueado Blanco, Natural)",
        verbose_name="Color / Acabado"
    )

    class Meta:
        verbose_name = "Características"
        verbose_name_plural = "Características"

    @property
    def en_stock(self):
        return self.stock > 0

    @property
    def dimensiones_texto(self):
        return f"{self.alto} x {self.ancho} x {self.profundidad} cm"

    def __str__(self):
        return f"Características de {self.mueble.nombre}"


# Modelos de Transacción

class Sucursal(EliminadoLogicoModel):
    nombre = models.CharField(
        max_length=120,
        unique=True,
        verbose_name="Nombre de la sucursal"
    )
    direccion = models.CharField(
        max_length=200,
        verbose_name="Dirección"
    )
    ciudad = models.CharField(
        max_length=100,
        default="Rio Cuarto",
        verbose_name="Ciudad"
    )
    provincia = models.CharField(
        max_length=100,
        default="Cordoba",
        verbose_name="Provincia"
    )
    telefono = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        verbose_name="Teléfono de contacto"
    )
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Email de contacto"
    )
    activa = models.BooleanField(
        default=True,
        verbose_name="Activa para operaciones"
    )

    class Meta:
        verbose_name = "Sucursal"
        verbose_name_plural = "Sucursales"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.ciudad})"


class MetodoPago(EliminadoLogicoModel):
    class TipoMetodo(models.TextChoices):
        EFECTIVO = 'EFECTIVO', 'Efectivo'
        TARJETA_DEBITO = 'TARJETA_DEBITO', 'Tarjeta de Débito'
        TARJETA_CREDITO = 'TARJETA_CREDITO', 'Tarjeta de Crédito'
        TRANSFERENCIA = 'TRANSFERENCIA', 'Transferencia Bancaria'
        MERCADO_PAGO = 'MERCADO_PAGO', 'Mercado Pago'

    nombre = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nombre del método"
    )
    tipo = models.CharField(
        max_length=30,
        choices=TipoMetodo.choices,
        default=TipoMetodo.TRANSFERENCIA,
        verbose_name="Tipo de pago"
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Habilitado"
    )
    instrucciones = models.TextField(
        blank=True,
        null=True,
        help_text="Instrucciones para el cliente (ej. datos de CBU o alias)",
        verbose_name="Instrucciones"
    )

    class Meta:
        verbose_name = "Método de Pago"
        verbose_name_plural = "Métodos de Pago"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"


class Pedido(EliminadoLogicoModel):
    class EstadoPedido(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente de Confirmación'
        PAGADO = 'PAGADO', 'Pagado'
        EN_PREPARACION = 'EN_PREPARACION', 'En Preparación'
        ENVIADO = 'ENVIADO', 'Enviado'
        ENTREGADO = 'ENTREGADO', 'Entregado'
        CANCELADO = 'CANCELADO', 'Cancelado'

    numero_pedido = models.PositiveIntegerField(
        unique=True,
        verbose_name="Número de pedido"
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='pedidos',
        verbose_name="Cliente"
    )
    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.PROTECT,
        related_name='pedidos',
        verbose_name="Sucursal de despacho"
    )
    metodo_pago = models.ForeignKey(
        MetodoPago,
        on_delete=models.PROTECT,
        related_name='pedidos',
        verbose_name="Método de pago"
    )
    estado = models.CharField(
        max_length=30,
        choices=EstadoPedido.choices,
        default=EstadoPedido.PENDIENTE,
        verbose_name="Estado"
    )
    direccion_entrega = models.CharField(
        max_length=255,
        verbose_name="Dirección de entrega"
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Monto total"
    )
    notas = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notas del pedido"
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Última actualización"
    )

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-fecha_creacion']

    def save(self, *args, **kwargs):
        if not self.numero_pedido:
            ultimo = Pedido.todos_los_objetos.order_by('-numero_pedido').first()
            self.numero_pedido = (ultimo.numero_pedido + 1) if ultimo and ultimo.numero_pedido else 1001
        super().save(*args, **kwargs)

    def actualizar_total(self):
        """Recalcula el total del pedido sumando los subtotales de sus detalles."""
        total = sum((d.subtotal for d in self.detalles.all()), Decimal('0.00'))
        self.total = total
        self.save(update_fields=['total'])
        return self.total

    def puede_cancelarse(self, horas_limite=24):
        """Valida si el pedido puede cancelarse según las reglas de negocio (plazo y estado)."""
        from django.utils import timezone
        from datetime import timedelta
        if self.estado == self.EstadoPedido.CANCELADO or self.eliminado_logico:
            return False
        if self.estado in [self.EstadoPedido.ENVIADO, self.EstadoPedido.ENTREGADO]:
            return False
        limite = self.fecha_creacion + timedelta(hours=horas_limite)
        return timezone.now() <= limite

    def cancelar(self):
        """Cancela el pedido: cambia el estado y realiza la baja lógica."""
        self.estado = self.EstadoPedido.CANCELADO
        self.eliminado_logico = True
        self.save(update_fields=['estado', 'eliminado_logico', 'fecha_actualizacion'])

    def __str__(self):
        return f"Pedido #{self.numero_pedido} - {self.cliente}"


class DetallePedido(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='detalles',
        verbose_name="Pedido"
    )
    mueble = models.ForeignKey(
        Mueble,
        on_delete=models.PROTECT,
        related_name='detalles_pedido',
        verbose_name="Mueble"
    )
    cantidad = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="Cantidad"
    )
    precio_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Precio unitario"
    )

    class Meta:
        verbose_name = "Detalle del Pedido"
        verbose_name_plural = "Detalles del Pedido"
        ordering = ['id']

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def save(self, *args, **kwargs):
        # Si no se especificó precio unitario, congelar el precio actual del mueble
        if (self.precio_unitario is None or self.precio_unitario == Decimal('0.00')) and hasattr(self.mueble, 'caracteristicas'):
            self.precio_unitario = self.mueble.caracteristicas.precio
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cantidad}x {self.mueble.nombre} (Pedido #{self.pedido.numero_pedido})"


