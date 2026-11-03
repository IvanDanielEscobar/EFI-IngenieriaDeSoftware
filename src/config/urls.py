from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from drf_spectacular.renderers import OpenApiJsonRenderer
from django.conf import settings
from django.conf.urls.static import static

class StandardOpenApiJsonRenderer(OpenApiJsonRenderer):
    media_type = 'application/json'

class SpectacularJSONAPIView(SpectacularAPIView):
    renderer_classes = [StandardOpenApiJsonRenderer]

urlpatterns = [
    path('', TemplateView.as_view(template_name='bienvenida.html'), name='bienvenida'),
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('api/', include('api.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/yaml/', SpectacularAPIView.as_view(), name='schema-yaml'),
    path('api/schema/json/', SpectacularJSONAPIView.as_view(), name='schema-json'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema-json'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema-json'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)