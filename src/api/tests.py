from decimal import Decimal
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import Usuario, Cliente, Categoria, Material, Mueble, Caracteristicas


class CatalogoPermisosYAuthTests(APITestCase):

    def setUp(self):
        # 1. Creación de los distintos roles y perfiles
        # Superadministrador
        self.superadmin = Usuario.objects.create_superuser(
            username='superadmin',
            email='superadmin@test.com',
            password='password123',
            rol=Usuario.Rol.EMPLEADO
        )

        # Administrador / Staff (no es superadmin)
        self.admin_staff = Usuario.objects.create_user(
            username='admin_staff',
            email='admin_staff@test.com',
            password='password123',
            rol=Usuario.Rol.EMPLEADO,
            is_staff=True,
            is_superuser=False
        )

        # Empleado Operativo (no es staff ni superadmin)
        self.empleado = Usuario.objects.create_user(
            username='empleado_operativo',
            email='empleado@test.com',
            password='password123',
            rol=Usuario.Rol.EMPLEADO,
            is_staff=False,
            is_superuser=False
        )

        # Cliente Minorista
        self.user_cliente_minorista = Usuario.objects.create_user(
            username='cliente_minorista',
            email='minorista@test.com',
            password='password123',
            rol=Usuario.Rol.CLIENTE
        )
        self.cliente_minorista = Cliente.objects.create(
            usuario=self.user_cliente_minorista,
            dni_cuit='20-11111111-2',
            es_mayorista=False
        )

        # Cliente Mayorista
        self.user_cliente_mayorista = Usuario.objects.create_user(
            username='cliente_mayorista',
            email='mayorista@test.com',
            password='password123',
            rol=Usuario.Rol.CLIENTE
        )
        self.cliente_mayorista = Cliente.objects.create(
            usuario=self.user_cliente_mayorista,
            dni_cuit='30-22222222-3',
            es_mayorista=True
        )

        # 2. Datos de prueba para catálogo
        self.categoria = Categoria.objects.create(
            nombre='Living Test',
            descripcion='Categoría para pruebas unitarias'
        )
        self.material = Material.objects.create(
            nombre='Madera Paraíso Test',
            descripcion='Material para pruebas'
        )
        self.mueble = Mueble.objects.create(
            nombre='Mesa Ratona Test',
            descripcion='Mesa de living',
            categoria=self.categoria,
            material=self.material
        )
        self.caracteristicas = Caracteristicas.objects.create(
            mueble=self.mueble,
            alto=Decimal('45.00'),
            ancho=Decimal('100.00'),
            profundidad=Decimal('60.00'),
            precio=Decimal('50000.00'),
            stock=10,
            color='Paraíso Natural'
        )

        self.url_categorias = reverse('categoria-list')
        self.url_muebles = reverse('mueble-list')
        self.url_token = reverse('token_obtain_pair')
        self.url_token_refresh = reverse('token_refresh')


    # Tests de Token JWT (SimpleJWT)

    def test_jwt_obtener_tokens_exitoso(self):
        """POST /api/token/ con credenciales válidas retorna tokens access y refresh."""
        data = {'username': 'empleado_operativo', 'password': 'password123'}
        response = self.client.post(self.url_token, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_jwt_credenciales_invalidas(self):
        """POST /api/token/ con contraseña incorrecta retorna 401."""
        data = {'username': 'empleado_operativo', 'password': 'clave_incorrecta'}
        response = self.client.post(self.url_token, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_jwt_refresh_token(self):
        """POST /api/token/refresh/ permite renovar un access token válido."""
        # 1. Obtener token
        res_login = self.client.post(self.url_token, {'username': 'admin_staff', 'password': 'password123'})
        refresh_token = res_login.data['refresh']

        # 2. Refrescar
        res_refresh = self.client.post(self.url_token_refresh, {'refresh': refresh_token}, format='json')
        self.assertEqual(res_refresh.status_code, status.HTTP_200_OK)
        self.assertIn('access', res_refresh.data)

    def test_jwt_autenticacion_en_endpoint(self):
        """Petición con header 'Authorization: Bearer <token>' autentica al usuario correctamente."""
        res_login = self.client.post(self.url_token, {'username': 'empleado_operativo', 'password': 'password123'})
        token = res_login.data['access']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        # Empleado puede crear categoría
        res = self.client.post(self.url_categorias, {'nombre': 'Dormitorio JWT', 'descripcion': 'Creada con JWT'})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)


    # Tests de Permisos

    def test_usuarios_anonimos_pueden_consultar_libremente(self):
        """Usuarios anónimos pueden listar categorías y muebles sin credenciales."""
        self.client.force_authenticate(user=None)
        res_cat = self.client.get(self.url_categorias)
        res_muebles = self.client.get(self.url_muebles)

        self.assertEqual(res_cat.status_code, status.HTTP_200_OK)
        self.assertEqual(res_muebles.status_code, status.HTTP_200_OK)

    def test_anonimo_no_puede_crear_categoria(self):
        """1. Usuario anónimo no puede crear categorías (retorna 401 Unauthorized)."""
        self.client.force_authenticate(user=None)
        res = self.client.post(self.url_categorias, {'nombre': 'Intento Anonimo'})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cliente_minorista_no_puede_crear_categoria(self):
        """2. Cliente minorista autenticado no puede crear categorías (retorna 403 Forbidden)."""
        self.client.force_authenticate(user=self.user_cliente_minorista)
        res = self.client.post(self.url_categorias, {'nombre': 'Intento Cliente'})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_empleado_puede_crear_y_modificar_categoria(self):
        """Usuarios con rol EMPLEADO pueden crear (POST) y modificar (PATCH/PUT) categorías."""
        self.client.force_authenticate(user=self.empleado)

        # Crear
        res_crear = self.client.post(self.url_categorias, {'nombre': 'Comedores Nuevos', 'descripcion': 'Desc'})
        self.assertEqual(res_crear.status_code, status.HTTP_201_CREATED)
        cat_id = res_crear.data['id']

        # Modificar
        url_detalle = reverse('categoria-detail', args=[cat_id])
        res_edit = self.client.patch(url_detalle, {'descripcion': 'Modificada por empleado'})
        self.assertEqual(res_edit.status_code, status.HTTP_200_OK)
        self.assertEqual(res_edit.data['descripcion'], 'Modificada por empleado')

    def test_empleado_no_administrador_no_puede_borrar(self):
        """Un empleado que no es administrador (is_staff=False) no puede borrar categorías (403)."""
        self.client.force_authenticate(user=self.empleado)
        url_detalle = reverse('categoria-detail', args=[self.categoria.id])
        res = self.client.delete(url_detalle)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        # La categoría debe permanecer activa
        self.categoria.refresh_from_db()
        self.assertFalse(self.categoria.eliminado_logico)

    def test_administrador_puede_realizar_baja_logica(self):
        """Un administrador (is_staff=True) puede realizar baja lógica mediante DELETE (204)."""
        self.client.force_authenticate(user=self.admin_staff)
        url_detalle = reverse('categoria-detail', args=[self.categoria.id])
        res = self.client.delete(url_detalle)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        # Comprobar que es un Soft Delete (no se eliminó físicamente de la base de datos)
        self.assertTrue(Categoria.todos_los_objetos.filter(id=self.categoria.id).exists())
        self.categoria.refresh_from_db()
        self.assertTrue(self.categoria.eliminado_logico)
        # Y no aparece en los objetos activos
        self.assertFalse(Categoria.objects.filter(id=self.categoria.id).exists())

    def test_eliminacion_definitiva_bloqueada_para_no_superadmin(self):
        """La eliminación definitiva (hard delete) está bloqueada para quien no sea superadmin."""
        cat_para_borrar = Categoria.objects.create(nombre='Categoria Temporal Para Borrado Fisico')
        url_hard_delete = reverse('categoria-borrado-fisico-endpoint', args=[cat_para_borrar.id])

        # Intento de administrador regular (staff)
        self.client.force_authenticate(user=self.admin_staff)
        res_admin = self.client.delete(url_hard_delete)
        self.assertEqual(res_admin.status_code, status.HTTP_403_FORBIDDEN)

        # Superadministrador sí puede
        self.client.force_authenticate(user=self.superadmin)
        res_super = self.client.delete(url_hard_delete)
        self.assertEqual(res_super.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Categoria.todos_los_objetos.filter(id=cat_para_borrar.id).exists())


    # Tests de Autenticación por Sesión

    def test_autenticacion_por_sesion_login_y_acceso(self):
        """Permite iniciar sesión con cookie de sesión (SessionAuthentication) y operar."""
        # Login de sesión
        login_exitoso = self.client.login(username='empleado_operativo', password='password123')
        self.assertTrue(login_exitoso)

        # Petición utilizando la sesión activa
        res = self.client.post(self.url_categorias, {'nombre': 'Categoría con Sesión'})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # Logout
        self.client.logout()
        res_post_logout = self.client.post(self.url_categorias, {'nombre': 'Intento post logout'})
        self.assertEqual(res_post_logout.status_code, status.HTTP_401_UNAUTHORIZED)