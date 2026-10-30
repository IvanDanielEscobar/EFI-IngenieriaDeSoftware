from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

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
    