from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MuebleViewSet, CategoriaViewSet, MaterialViewSet

router = DefaultRouter()
router.register(r'muebles', MuebleViewSet, basename='mueble')
router.register(r'categorias', CategoriaViewSet, basename='categoria')
router.register(r'materiales', MaterialViewSet, basename='material')

urlpatterns = [
    path('', include(router.urls)),
]
