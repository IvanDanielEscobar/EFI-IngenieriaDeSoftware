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


# ==============================================================================
# Modelos del Catálogo de Mueblería
# ==============================================================================

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

    