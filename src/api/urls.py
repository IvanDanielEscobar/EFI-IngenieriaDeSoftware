from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import (
    MuebleViewSet,
    CategoriaViewSet,
    MaterialViewSet,
    SucursalViewSet,
    MetodoPagoViewSet,
    ClienteViewSet,
    CaracteristicasViewSet,
    PedidoViewSet,
    DetallePedidoViewSet,
)

router = DefaultRouter()
router.register(r'muebles', MuebleViewSet, basename='mueble')
router.register(r'categorias', CategoriaViewSet, basename='categoria')
router.register(r'materiales', MaterialViewSet, basename='material')
router.register(r'sucursales', SucursalViewSet, basename='sucursal')
router.register(r'metodos-pago', MetodoPagoViewSet, basename='metodopago')
router.register(r'clientes', ClienteViewSet, basename='cliente')
router.register(r'caracteristicas', CaracteristicasViewSet, basename='caracteristicas')
router.register(r'pedidos', PedidoViewSet, basename='pedido')
router.register(r'detalles-pedido', DetallePedidoViewSet, basename='detallepedido')

urlpatterns = [
    # Endpoints de Autenticación SimpleJWT
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Enrutamiento de ViewSets
    path('', include(router.urls)),
]
