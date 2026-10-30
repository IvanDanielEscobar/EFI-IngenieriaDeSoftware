from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Cliente

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Rol del Sistema', {'fields': ('rol',)}),
    )
    list_display = ['username', 'email', 'rol', 'is_staff', 'is_active']
    list_filter = ['rol', 'is_staff', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'dni_cuit', 'telefono', 'es_mayorista', 'fecha_creacion']
    list_filter = ['es_mayorista', 'fecha_creacion']
    search_fields = ['usuario__username', 'usuario__email', 'dni_cuit', 'telefono']