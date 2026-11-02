from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction

from api.models import (
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


class Command(BaseCommand):
    help = "Puebla la base de datos con información inicial para el catálogo de muebles, transacciones y usuarios."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Iniciando la carga de datos iniciales..."))



        # 1. Usuarios y Perfiles de Clientes

        self.stdout.write("-> Creando usuarios y clientes...")

        # Superadministrador
        admin_user, created = Usuario.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@homedeco.com",
                "first_name": "Administrador",
                "last_name": "General",
                "rol": Usuario.Rol.EMPLEADO,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            admin_user.set_password("admin123")
            admin_user.save()

        # Empleado
        empleado_user, created = Usuario.objects.get_or_create(
            username="vendedor1",
            defaults={
                "email": "vendedor1@homedeco.com",
                "first_name": "Marcos",
                "last_name": "Ventas",
                "rol": Usuario.Rol.EMPLEADO,
                "is_staff": True,
            },
        )
        if created:
            empleado_user.set_password("vendedor123")
            empleado_user.save()

        # Cliente Final
        cliente_user1, created = Usuario.objects.get_or_create(
            username="cliente_juan",
            defaults={
                "email": "juan.perez@gmail.com",
                "first_name": "Juan",
                "last_name": "Pérez",
                "rol": Usuario.Rol.CLIENTE,
            },
        )
        if created:
            cliente_user1.set_password("cliente123")
            cliente_user1.save()

        cliente_juan, _ = Cliente.objects.get_or_create(
            usuario=cliente_user1,
            defaults={
                "dni_cuit": "20-35111222-4",
                "telefono": "0358-4612345",
                "direccion": "Av. España 1230, Río Cuarto",
                "es_mayorista": False,
            },
        )

        # Cliente Mayorista
        cliente_user2, created = Usuario.objects.get_or_create(
            username="cliente_deco_hogar",
            defaults={
                "email": "compras@decolux.com.ar",
                "first_name": "Deco Lux",
                "last_name": "Comercial",
                "rol": Usuario.Rol.CLIENTE,
            },
        )
        if created:
            cliente_user2.set_password("deco123")
            cliente_user2.save()

        cliente_mayorista, _ = Cliente.objects.get_or_create(
            usuario=cliente_user2,
            defaults={
                "dni_cuit": "30-71555666-8",
                "telefono": "0351-4229988",
                "direccion": "Bv. San Juan 550, Córdoba Capital",
                "es_mayorista": True,
            },
        )

        # 2. Categorías

        self.stdout.write("-> Creando categorías...")
        categorias_data = [
            ("Living & Confort", "Sillones, mesas ratonas y muebles para sala de estar"),
            ("Comedor", "Mesas de comedor, sillas, vajilleros y barras"),
            ("Dormitorio", "Camas, respaldos, mesas de noche y cómodas"),
            ("Oficina & Estudio", "Escritorios ergonómicos, bibliotecas y organizadores"),
            ("Exterior & Jardín", "Mobiliario resistente para galerías, patios y terrazas"),
        ]
        categorias = {}
        for nombre, desc in categorias_data:
            cat, _ = Categoria.todos_los_objetos.get_or_create(
                nombre=nombre, defaults={"descripcion": desc, "eliminado_logico": False}
            )
            categorias[nombre] = cat


        # 3. Materiales

        self.stdout.write("-> Creando materiales...")
        materiales_data = [
            ("Madera de Paraíso", "Madera semidura de veta vistosa y cálida"),
            ("Roble Macizo", "Madera noble de alta densidad y durabilidad superior"),
            ("Hierro Estructural", "Perfiles de acero con pintura epoxi al horno"),
            ("MDF Laqueado", "Tablero de densidad media con terminación poliuretánica"),
            ("Petiribí", "Madera autóctona de tono castaño claro y excelente brillo natural"),
        ]
        materiales = {}
        for nombre, desc in materiales_data:
            mat, _ = Material.todos_los_objetos.get_or_create(
                nombre=nombre, defaults={"descripcion": desc, "eliminado_logico": False}
            )
            materiales[nombre] = mat


        # 4. Muebles y Fichas Técnicas (12 ítems para probar paginación de 10)

        self.stdout.write("-> Creando catálogo de muebles y fichas técnicas...")
        muebles_data = [
            {
                "nombre": "Mesa Comedor Nórdica Paraíso",
                "categoria": categorias["Comedor"],
                "material": materiales["Madera de Paraíso"],
                "descripcion": "Mesa fija para 6 u 8 personas con bordes redondeados y patas en ángulo.",
                "caracteristicas": {
                    "alto": Decimal("75.00"),
                    "ancho": Decimal("160.00"),
                    "profundidad": Decimal("90.00"),
                    "peso": Decimal("32.00"),
                    "precio": Decimal("185000.00"),
                    "stock": 10,
                    "color": "Paraíso Lustre Natural",
                },
            },
            {
                "nombre": "Silla Dinamarca Tapizada",
                "categoria": categorias["Comedor"],
                "material": materiales["Madera de Paraíso"],
                "descripcion": "Estructura ergonómica en paraíso macizo y asiento tapizado en lino antimanchas.",
                "caracteristicas": {
                    "alto": Decimal("85.00"),
                    "ancho": Decimal("48.00"),
                    "profundidad": Decimal("52.00"),
                    "peso": Decimal("6.50"),
                    "precio": Decimal("45000.00"),
                    "stock": 40,
                    "color": "Lino Gris Claro",
                },
            },
            {
                "nombre": "Rack TV Escandinavo",
                "categoria": categorias["Living & Confort"],
                "material": materiales["Madera de Paraíso"],
                "descripcion": "Mueble bajo con dos puertas corredizas y estante pasacables central.",
                "caracteristicas": {
                    "alto": Decimal("55.00"),
                    "ancho": Decimal("180.00"),
                    "profundidad": Decimal("40.00"),
                    "peso": Decimal("28.00"),
                    "precio": Decimal("130000.00"),
                    "stock": 8,
                    "color": "Paraíso con Frentes Blancos",
                },
            },
            {
                "nombre": "Sillón Chesterfield 3 Cuerpos",
                "categoria": categorias["Living & Confort"],
                "material": materiales["Roble Macizo"],
                "descripcion": "Clásico sofá con tapizado capitoné artesanal y estructura interna reforzada.",
                "caracteristicas": {
                    "alto": Decimal("80.00"),
                    "ancho": Decimal("210.00"),
                    "profundidad": Decimal("90.00"),
                    "peso": Decimal("55.00"),
                    "precio": Decimal("320000.00"),
                    "stock": 4,
                    "color": "Cuero Suela Envejecido",
                },
            },
            {
                "nombre": "Mesa Ratona Industrial",
                "categoria": categorias["Living & Confort"],
                "material": materiales["Hierro Estructural"],
                "descripcion": "Tapa de madera rústica combinada con base geométrica de hierro negro.",
                "caracteristicas": {
                    "alto": Decimal("45.00"),
                    "ancho": Decimal("100.00"),
                    "profundidad": Decimal("60.00"),
                    "peso": Decimal("16.00"),
                    "precio": Decimal("68000.00"),
                    "stock": 15,
                    "color": "Negro Microtexturado y Madera",
                },
            },
            {
                "nombre": "Escritorio Home Office Minimalista",
                "categoria": categorias["Oficina & Estudio"],
                "material": materiales["Madera de Paraíso"],
                "descripcion": "Diseño depurado con pasacables integrado y cajón secreto para laptop.",
                "caracteristicas": {
                    "alto": Decimal("76.00"),
                    "ancho": Decimal("120.00"),
                    "profundidad": Decimal("60.00"),
                    "peso": Decimal("22.00"),
                    "precio": Decimal("95000.00"),
                    "stock": 12,
                    "color": "Madera Clara Poliuretánica",
                },
            },
            {
                "nombre": "Biblioteca Modular 5 Niveles",
                "categoria": categorias["Oficina & Estudio"],
                "material": materiales["Hierro Estructural"],
                "descripcion": "Estructura vertical resistente apta para libros pesados y elementos decorativos.",
                "caracteristicas": {
                    "alto": Decimal("190.00"),
                    "ancho": Decimal("90.00"),
                    "profundidad": Decimal("35.00"),
                    "peso": Decimal("38.00"),
                    "precio": Decimal("115000.00"),
                    "stock": 7,
                    "color": "Estructura Negra con Estantes Cálidos",
                },
            },
            {
                "nombre": "Cama King Size con Respaldo",
                "categoria": categorias["Dormitorio"],
                "material": materiales["Petiribí"],
                "descripcion": "Cama para colchón de 2x2m con largueros reforzados y respaldo macizo continuo.",
                "caracteristicas": {
                    "alto": Decimal("110.00"),
                    "ancho": Decimal("205.00"),
                    "profundidad": Decimal("210.00"),
                    "peso": Decimal("65.00"),
                    "precio": Decimal("240000.00"),
                    "stock": 3,
                    "color": "Petiribí Hidrolaqueado",
                },
            },
            {
                "nombre": "Mesa de Noche Flotante",
                "categoria": categorias["Dormitorio"],
                "material": materiales["MDF Laqueado"],
                "descripcion": "Mesa de luz aérea con anclaje invisible a pared y cajón de apertura suave.",
                "caracteristicas": {
                    "alto": Decimal("20.00"),
                    "ancho": Decimal("45.00"),
                    "profundidad": Decimal("35.00"),
                    "peso": Decimal("7.00"),
                    "precio": Decimal("38000.00"),
                    "stock": 18,
                    "color": "Blanco Satinado",
                },
            },
            {
                "nombre": "Cómoda 6 Cajones Escandinava",
                "categoria": categorias["Dormitorio"],
                "material": materiales["Roble Macizo"],
                "descripcion": "Cajonera espaciosa con guías telescópicas y tiradores embutidos.",
                "caracteristicas": {
                    "alto": Decimal("90.00"),
                    "ancho": Decimal("130.00"),
                    "profundidad": Decimal("45.00"),
                    "peso": Decimal("48.00"),
                    "precio": Decimal("175000.00"),
                    "stock": 5,
                    "color": "Roble Claro Natural",
                },
            },
            {
                "nombre": "Barra Desayunadora Alta",
                "categoria": categorias["Comedor"],
                "material": materiales["Hierro Estructural"],
                "descripcion": "Mesa alta tipo bar ideal para cocinas integradas o monoambientes.",
                "caracteristicas": {
                    "alto": Decimal("100.00"),
                    "ancho": Decimal("120.00"),
                    "profundidad": Decimal("50.00"),
                    "peso": Decimal("20.00"),
                    "precio": Decimal("82000.00"),
                    "stock": 9,
                    "color": "Hierro Negro Mate y Madera",
                },
            },
            {
                "nombre": "Banco de Jardín Plaza",
                "categoria": categorias["Exterior & Jardín"],
                "material": materiales["Hierro Estructural"],
                "descripcion": "Banco exterior con tratamiento intemperie y listones anticorrosivos.",
                "caracteristicas": {
                    "alto": Decimal("80.00"),
                    "ancho": Decimal("150.00"),
                    "profundidad": Decimal("60.00"),
                    "peso": Decimal("24.00"),
                    "precio": Decimal("74000.00"),
                    "stock": 12,
                    "color": "Negro Forja Antióxido",
                },
            },
        ]

        muebles = {}
        for m_data in muebles_data:
            mueble, _ = Mueble.todos_los_objetos.get_or_create(
                nombre=m_data["nombre"],
                defaults={
                    "categoria": m_data["categoria"],
                    "material": m_data["material"],
                    "descripcion": m_data["descripcion"],
                    "eliminado_logico": False,
                },
            )
            # Ficha técnica
            c_data = m_data["caracteristicas"]
            Caracteristicas.objects.update_or_create(
                mueble=mueble,
                defaults={
                    "alto": c_data["alto"],
                    "ancho": c_data["ancho"],
                    "profundidad": c_data["profundidad"],
                    "peso": c_data["peso"],
                    "precio": c_data["precio"],
                    "stock": c_data["stock"],
                    "color": c_data["color"],
                },
            )
            muebles[mueble.nombre] = mueble


        # 5. Sucursales

        self.stdout.write("-> Creando sucursales...")
        sucursales_data = [
            ("Sucursal Central Río Cuarto", "Alvear 540", "Rio Cuarto", "Cordoba", "0358-4641122", "central@homedeco.com"),
            ("Sucursal Córdoba Capital", "Av. Colón 1890", "Cordoba", "Cordoba", "0351-4223344", "cordoba@homedeco.com"),
            ("Sucursal Villa María", "Bv. España 310", "Villa Maria", "Cordoba", "0353-4532211", "villamaria@homedeco.com"),
        ]
        sucursales = {}
        for nom, dir_s, ciu, prov, tel, mail in sucursales_data:
            suc, _ = Sucursal.todos_los_objetos.get_or_create(
                nombre=nom,
                defaults={
                    "direccion": dir_s,
                    "ciudad": ciu,
                    "provincia": prov,
                    "telefono": tel,
                    "email": mail,
                    "activa": True,
                    "eliminado_logico": False,
                },
            )
            sucursales[nom] = suc


        # 6. Métodos de Pago

        self.stdout.write("-> Creando métodos de pago...")
        metodos_data = [
            ("Transferencia Bancaria Inmediata", MetodoPago.TipoMetodo.TRANSFERENCIA, "CBU: 0110456788889999000123 - Alias: HOME.DECO.RIO4"),
            ("Mercado Pago", MetodoPago.TipoMetodo.MERCADO_PAGO, "Transferencia o dinero en cuenta al alias: deco.muebles.mp"),
            ("Tarjeta de Crédito en Cuotas", MetodoPago.TipoMetodo.TARJETA_CREDITO, "Aceptamos Visa y Mastercard en hasta 6 cuotas fijas"),
            ("Efectivo en Salón / Contra Entrega", MetodoPago.TipoMetodo.EFECTIVO, "Abono físico al retirar en sucursal o recibir el flete"),
        ]
        metodos = {}
        for nom, tipo, inst in metodos_data:
            met, _ = MetodoPago.todos_los_objetos.get_or_create(
                nombre=nom,
                defaults={"tipo": tipo, "instrucciones": inst, "activo": True, "eliminado_logico": False},
            )
            metodos[nom] = met


        # 7. Pedidos y Ventas Históricas (Alimenta /api/muebles/destacados/)

        self.stdout.write("-> Creando pedidos y detalles de venta...")

        # Pedido 1001: Pagado (1 mesa nórdica + 6 sillas dinamarca)
        ped1, _ = Pedido.todos_los_objetos.get_or_create(
            numero_pedido=1001,
            defaults={
                "cliente": cliente_juan,
                "sucursal": sucursales["Sucursal Central Río Cuarto"],
                "metodo_pago": metodos["Transferencia Bancaria Inmediata"],
                "estado": Pedido.EstadoPedido.PAGADO,
                "direccion_entrega": "Av. España 1230, Río Cuarto",
                "notas": "Entregar después de las 16hs.",
                "eliminado_logico": False,
            },
        )
        DetallePedido.objects.get_or_create(
            pedido=ped1,
            mueble=muebles["Mesa Comedor Nórdica Paraíso"],
            defaults={"cantidad": 1, "precio_unitario": Decimal("185000.00")},
        )
        DetallePedido.objects.get_or_create(
            pedido=ped1,
            mueble=muebles["Silla Dinamarca Tapizada"],
            defaults={"cantidad": 6, "precio_unitario": Decimal("45000.00")},
        )
        ped1.actualizar_total()

        # Pedido 1002: Entregado (Mayorista compra 2 racks TV + 1 mesa ratona)
        ped2, _ = Pedido.todos_los_objetos.get_or_create(
            numero_pedido=1002,
            defaults={
                "cliente": cliente_mayorista,
                "sucursal": sucursales["Sucursal Córdoba Capital"],
                "metodo_pago": metodos["Mercado Pago"],
                "estado": Pedido.EstadoPedido.ENTREGADO,
                "direccion_entrega": "Bv. San Juan 550, Córdoba Capital",
                "notas": "Despacho con remito mayorista.",
                "eliminado_logico": False,
            },
        )
        DetallePedido.objects.get_or_create(
            pedido=ped2,
            mueble=muebles["Rack TV Escandinavo"],
            defaults={"cantidad": 2, "precio_unitario": Decimal("130000.00")},
        )
        DetallePedido.objects.get_or_create(
            pedido=ped2,
            mueble=muebles["Mesa Ratona Industrial"],
            defaults={"cantidad": 1, "precio_unitario": Decimal("68000.00")},
        )
        ped2.actualizar_total()

        # Pedido 1003: En preparación (cliente juan compra 4 sillas dinamarca más)
        ped3, _ = Pedido.todos_los_objetos.get_or_create(
            numero_pedido=1003,
            defaults={
                "cliente": cliente_juan,
                "sucursal": sucursales["Sucursal Villa María"],
                "metodo_pago": metodos["Tarjeta de Crédito en Cuotas"],
                "estado": Pedido.EstadoPedido.EN_PREPARACION,
                "direccion_entrega": "Av. España 1230, Río Cuarto",
                "notas": "Retiro por sucursal Villa María.",
                "eliminado_logico": False,
            },
        )
        DetallePedido.objects.get_or_create(
            pedido=ped3,
            mueble=muebles["Silla Dinamarca Tapizada"],
            defaults={"cantidad": 4, "precio_unitario": Decimal("45000.00")},
        )
        ped3.actualizar_total()

        self.stdout.write(self.style.SUCCESS("✓ Carga de datos iniciales finalizada con éxito."))
        self.stdout.write(self.style.SUCCESS("  - Superusuario: admin / admin123"))
        self.stdout.write(self.style.SUCCESS("  - Empleado: vendedor1 / vendedor123"))
        self.stdout.write(self.style.SUCCESS("  - Clientes: cliente_juan (clave: cliente123) y cliente_deco_hogar (clave: deco123)"))
        self.stdout.write(self.style.SUCCESS("  - Total muebles cargados: 12 (comprueba paginación de 10)"))
        self.stdout.write(self.style.SUCCESS("  - Ranking ventas: Silla Dinamarca (10 unidades), Rack TV (2 unidades), Mesa Nórdica (1 unidad)"))