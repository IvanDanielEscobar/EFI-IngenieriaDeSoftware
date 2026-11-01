from django.urls import path, include
from rest_framework.routers import DefaultRouter
 
from .views import (
    MuebleViewSet,
    CategoriaViewSet,
    MaterialViewSet,
    SucursalViewSet,
    MetodoPagoViewSet,
    ClienteViewSet,
    CaracteristicasViewSet,
    PedidoViewSet,
)

router = DefaultRouter()
router.register(r'muebles', MuebleViewSet, basename='mueble')
router.register(r'categorias', CategoriaViewSet, basename='categoria')
router.register(r'materiales', MaterialViewSet, basename='material')
router.register(r'pedidos', PedidoViewSet, basename='pedido')
router.register(r'sucursales', SucursalViewSet, basename='sucursal')
router.register(r'metodos-pago', MetodoPagoViewSet, basename='metodopago')
router.register(r'clientes', ClienteViewSet, basename='cliente')
router.register(r'caracteristicas', CaracteristicasViewSet, basename='caracteristicas')

urlpatterns = [
    path('', include(router.urls)),
]
