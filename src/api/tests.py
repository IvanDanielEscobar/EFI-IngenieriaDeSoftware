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


class RegistroYRolesUsuariosTests(APITestCase):
    """
    Pruebas automatizadas para el registro de clientes, creación de usuarios por rol
    y restricciones de administradores sin borrado físico.
    """

    def setUp(self):
        # Superadministrador
        self.superadmin = Usuario.objects.create_superuser(
            username='test_superadmin',
            email='super@test.com',
            password='password123',
            rol=Usuario.Rol.ADMIN
        )

        # Administrador (rol ADMIN, sin is_superuser)
        self.admin_operativo = Usuario.objects.create_user(
            username='test_admin',
            email='admin_op@test.com',
            password='password123',
            rol=Usuario.Rol.ADMIN,
            is_staff=True,
            is_superuser=False
        )

        # Empleado
        self.empleado = Usuario.objects.create_user(
            username='test_empleado',
            email='empleado_op@test.com',
            password='password123',
            rol=Usuario.Rol.EMPLEADO,
            is_staff=True,
            is_superuser=False
        )

        # Cliente
        self.cliente_user = Usuario.objects.create_user(
            username='test_cliente',
            email='cliente_op@test.com',
            password='password123',
            rol=Usuario.Rol.CLIENTE
        )
        self.cliente = Cliente.objects.create(
            usuario=self.cliente_user,
            dni_cuit='20-44555666-7',
            telefono='0358-4561234',
            direccion='Colón 150',
            es_mayorista=False
        )

        self.url_registro = reverse('registro_cliente')
        self.url_usuarios = reverse('usuario-list')
        self.url_clientes = reverse('cliente-list')

    def test_registro_publico_cliente_exitoso(self):
        """Un visitante anónimo puede registrarse como cliente desde la tienda web."""
        payload = {
            'username': 'nuevo_cliente_web',
            'email': 'nuevo_cliente@test.com',
            'password': 'PasswordValida123!',
            'first_name': 'Camila',
            'last_name': 'Torres',
            'dni_cuit': '27-38999888-4',
            'telefono': '0358-154998877',
            'direccion': 'San Martín 500',
            'es_mayorista': False,
        }
        res = self.client.post(self.url_registro, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', res.data)
        self.assertIn('access', res.data['tokens'])
        self.assertEqual(res.data['usuario']['username'], 'nuevo_cliente_web')
        self.assertEqual(res.data['usuario']['rol'], 'CLIENTE')

        # Comprobar que se crearon Usuario y Cliente
        self.assertTrue(Usuario.objects.filter(username='nuevo_cliente_web').exists())
        self.assertTrue(Cliente.objects.filter(dni_cuit='27-38999888-4').exists())

    def test_registro_cliente_dni_duplicado_falla(self):
        """No permite registrar un cliente con DNI/CUIT existente."""
        payload = {
            'username': 'otro_cliente',
            'email': 'otro@test.com',
            'password': 'PasswordValida123!',
            'dni_cuit': '20-44555666-7',  # Ya existente
        }
        res = self.client.post(self.url_registro, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('dni_cuit', res.data)

    def test_empleado_puede_crear_cliente(self):
        """Un empleado puede registrar un nuevo cliente en el sistema."""
        self.client.force_authenticate(user=self.empleado)
        payload = {
            'username': 'cliente_creado_por_empleado',
            'password': 'PasswordValida123!',
            'email': 'cliente_creado@test.com',
            'first_name': 'Lucía',
            'last_name': 'Méndez',
            'dni_cuit': '27-35111333-9',
            'telefono': '0358-4632145',
            'direccion': 'Alvear 890',
            'es_mayorista': True,
        }
        res = self.client.post(self.url_clientes, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['dni_cuit'], '27-35111333-9')
        self.assertEqual(res.data['usuario_username'], 'cliente_creado_por_empleado')

    def test_cliente_no_puede_crear_otros_clientes(self):
        """Un cliente común no tiene permisos para dar de alta clientes por la API administrativa."""
        self.client.force_authenticate(user=self.cliente_user)
        res = self.client.post(self.url_clientes, {'dni_cuit': '20-99888777-1'})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_superadmin_o_admin_crea_empleado(self):
        """Un administrador puede crear un usuario y otorgarle rol de EMPLEADO."""
        self.client.force_authenticate(user=self.admin_operativo)
        payload = {
            'username': 'nuevo_vendedor_sucursal',
            'email': 'vendedor_nuevo@homedeco.com',
            'password': 'PasswordValida123!',
            'first_name': 'Esteban',
            'last_name': 'Quito',
            'rol': 'EMPLEADO',
        }
        res = self.client.post(self.url_usuarios, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['rol'], 'EMPLEADO')
        self.assertTrue(res.data['is_staff'])

        creado = Usuario.objects.get(username='nuevo_vendedor_sucursal')
        self.assertEqual(creado.rol, Usuario.Rol.EMPLEADO)
        self.assertTrue(creado.es_empleado())

    def test_empleado_no_puede_gestionar_usuarios(self):
        """Un empleado común no tiene acceso al endpoint de gestión de usuarios."""
        self.client.force_authenticate(user=self.empleado)
        res = self.client.get(self.url_usuarios)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_no_puede_hacer_borrado_fisico(self):
        """Un usuario con rol ADMIN puede hacer baja lógica pero NO borrado físico."""
        cat = Categoria.objects.create(nombre='Cat Para Prueba Admin Borrado')
        url_borrado_fisico = reverse('categoria-borrado-fisico-endpoint', args=[cat.id])
        url_borrado_logico = reverse('categoria-detail', args=[cat.id])

        self.client.force_authenticate(user=self.admin_operativo)

        # 1. Borrado físico denegado para ADMIN no superuser
        res_fisico = self.client.delete(url_borrado_fisico)
        self.assertEqual(res_fisico.status_code, status.HTTP_403_FORBIDDEN)

        # 2. Borrado lógico estándar permitido
        res_logico = self.client.delete(url_borrado_logico)
        self.assertEqual(res_logico.status_code, status.HTTP_204_NO_CONTENT)

        cat.refresh_from_db()
        self.assertTrue(cat.eliminado_logico)

    def test_usuario_puede_consultar_su_propio_perfil(self):
        """Cualquier usuario autenticado puede consultar su propio perfil en /api/usuarios/perfil/."""
        url_perfil = reverse('usuario-perfil')
        self.client.force_authenticate(user=self.cliente_user)
        res = self.client.get(url_perfil)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['username'], 'test_cliente')
        self.assertIsNotNone(res.data['cliente'])
        self.assertEqual(res.data['cliente']['dni_cuit'], '20-44555666-7')
