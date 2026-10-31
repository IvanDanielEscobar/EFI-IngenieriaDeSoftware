from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Usuario,
    Cliente,
    Categoria,
    Material,
    Mueble,
    Caracteristicas,
    Sucursal,
    MetodoPago,
    Pedido,
    DetallePedido,
)


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


# Catalogo de Muebles

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion', 'eliminado_logico']
    list_filter = ['eliminado_logico']
    search_fields = ['nombre', 'descripcion']


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion', 'eliminado_logico']
    list_filter = ['eliminado_logico']
    search_fields = ['nombre', 'descripcion']


class CaracteristicasInline(admin.StackedInline):
    model = Caracteristicas
    can_delete = False
    verbose_name = "Características y Precio"
    verbose_name_plural = "Características y Precio"


@admin.register(Mueble)
class MuebleAdmin(admin.ModelAdmin):
    list_display = [
        'nombre',
        'categoria',
        'material',
        'get_precio',
        'get_stock',
        'eliminado_logico',
        'fecha_creacion',
    ]
    list_filter = ['categoria', 'material', 'eliminado_logico', 'fecha_creacion']
    search_fields = ['nombre', 'descripcion']
    inlines = [CaracteristicasInline]

    @admin.display(description="Precio ARS")
    def get_precio(self, obj):
        return f"${obj.caracteristicas.precio}" if hasattr(obj, 'caracteristicas') else "-"

    @admin.display(description="Stock")
    def get_stock(self, obj):
        return obj.caracteristicas.stock if hasattr(obj, 'caracteristicas') else "-"

# Transacciones: Sucursales, Métodos de Pago y Pedidos

@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'ciudad', 'provincia', 'telefono', 'activa', 'eliminado_logico']
    list_filter = ['activa', 'ciudad', 'eliminado_logico']
    search_fields = ['nombre', 'ciudad', 'direccion', 'telefono']


@admin.register(MetodoPago)
class MetodoPagoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'activo', 'eliminado_logico']
    list_filter = ['tipo', 'activo', 'eliminado_logico']
    search_fields = ['nombre', 'tipo']


class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 1
    readonly_fields = ['get_subtotal']
    fields = ['mueble', 'cantidad', 'precio_unitario', 'get_subtotal']

    @admin.display(description="Subtotal")
    def get_subtotal(self, obj):
        return f"${obj.subtotal:.2f}" if obj and obj.id else "-"


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = [
        'numero_pedido',
        'cliente',
        'sucursal',
        'metodo_pago',
        'estado',
        'total',
        'eliminado_logico',
        'fecha_creacion',
    ]
    list_filter = [
        'estado',
        'sucursal',
        'metodo_pago',
        'eliminado_logico',
        'fecha_creacion',
    ]
    search_fields = [
        'numero_pedido',
        'cliente__usuario__username',
        'cliente__dni_cuit',
        'direccion_entrega',
    ]
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    inlines = [DetallePedidoInline]
