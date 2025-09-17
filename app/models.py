from datetime import datetime
from app import db
from flask_login import UserMixin
from decimal import Decimal
import mysql.connector
from flask import current_app
from werkzeug.security import generate_password_hash


# ✅ Modelo Usuario
class Usuario(db.Model, UserMixin):

    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    documento = db.Column(db.String(50), unique=True, nullable=False)  
    nombre = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    direccion = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(20), nullable=False)
    estado = db.Column(db.String(10), default='activo') 
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password = generate_password_hash(
            password,
            method='scrypt',
            salt_length=16
        )
    def __repr__(self):
        return f'<Usuario {self.documento}>'


# ✅ Modelo CategoriaComponente
class CategoriaComponente(db.Model):
    __tablename__ = 'categorias_componentes'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    icono = db.Column(db.String(100))
    nivel_prioridad = db.Column(db.Integer)

    # Relación con Producto
    componentes = db.relationship('Producto', back_populates='categoria', lazy=True)


# ✅ Modelo Producto
class Producto(db.Model):
    __tablename__ = 'componentes'

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(100), unique=True, nullable=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    publicado = db.Column(db.Boolean, default=False)
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    costo = db.Column(db.Numeric(10, 2), nullable=True)
    stock = db.Column(db.Integer, nullable=True)
    stock_minimo = db.Column(db.Integer, nullable=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias_componentes.id'), nullable=True)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    especificaciones = db.Column(db.Text, nullable=True)
    garantia_meses = db.Column(db.Integer, nullable=True)
    imagen_url = db.Column(db.String(255), nullable=True)
    estado = db.Column(db.String(20), default='Nuevo')
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow)
    ubicacion = db.Column(db.String(100), nullable=True)

    # Relación inversa
    categoria = db.relationship('CategoriaComponente', back_populates='componentes')
    proveedor = db.relationship('Usuario', foreign_keys=[proveedor_id])

    def __repr__(self):
        return f'<Producto {self.nombre}>'

# ✅ Modelo Servicio
class Servicio(db.Model):
    __tablename__ = 'servicios'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(100), unique=True, nullable=True)
    nombre = db.Column(db.String(100), nullable=True)
    descripcion = db.Column(db.Text, nullable=True)
    tipo = db.Column(db.String(100), nullable=True)
    precio_base = db.Column(db.Numeric(10, 2), nullable=True)
    duracion_estimada = db.Column(db.String(255), nullable=True)
    requisitos = db.Column(db.String(255), nullable=False)
    garantia_meses = db.Column(db.Integer, nullable=True)
    estado = db.Column(db.String(20), default='activo')

    def __repr__(self):
        return f'<Servicio {self.codigo}>'

# ✅ Modelo Facturas
class Factura(db.Model):
    __tablename__ = 'facturas'

    id = db.Column(db.Integer, primary_key=True)
    numero_factura = db.Column(db.String(20), unique=True, nullable=False)  # 'FAC-2024-001'
    cliente_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    orden_servicio_id = db.Column(db.Integer, db.ForeignKey('ordenes_servicio.id'), nullable=True)
    cotizacion_id = db.Column(db.Integer, db.ForeignKey('cotizaciones.id'), nullable=True)
    subtotal = db.Column(db.Integer, nullable=False)
    iva = db.Column(db.Integer, nullable=False)  # Valor en COP
    total = db.Column(db.Integer, nullable=False)
    metodo_pago = db.Column(db.Enum('efectivo', 'transferencia', 'tarjeta'), nullable=False)
    fecha_emision = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    cliente = db.relationship('Usuario', foreign_keys=[cliente_id])
    orden_servicio = db.relationship('OrdenServicio', foreign_keys=[orden_servicio_id])
    cotizacion = db.relationship('Cotizacion', foreign_keys=[cotizacion_id])
    detalles = db.relationship('DetalleFactura', backref='factura', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Factura {self.numero_factura}>'
    
# ✅ Modelo DetalleFactura
class DetalleFactura(db.Model):
    __tablename__ = 'detalle_factura'

    id = db.Column(db.Integer, primary_key=True)
    factura_id = db.Column(db.Integer, db.ForeignKey('facturas.id'), nullable=False)
    componente_id = db.Column(db.Integer, db.ForeignKey('componentes.id'), nullable=True)  # Cambia a nullable=True
    servicio_id = db.Column(db.Integer, db.ForeignKey('servicios.id'), nullable=True)      # Cambia a nullable=True
    cantidad = db.Column(db.Integer, nullable=False, default=1)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)

    # Relaciones para mostrar nombre en la factura
    componente = db.relationship('Producto', foreign_keys=[componente_id])
    servicio = db.relationship('Servicio', foreign_keys=[servicio_id])

# ✅ Modelo MovimientoInventario
class MovimientoInventario(db.Model):
    __tablename__ = 'movimientos_inventario'

    id = db.Column(db.Integer, primary_key=True)
    componente_id = db.Column(db.Integer, db.ForeignKey('componentes.id'), nullable=False)
    tipo = db.Column(db.Enum('entrada', 'salida', 'ajuste', 'devolucion'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    responsable_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    orden_servicio_id = db.Column(db.Integer, db.ForeignKey('ordenes_servicio.id'), nullable=True)
    referencia = db.Column(db.String(50))
    motivo = db.Column(db.String(200), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)


    # Relaciones opcionales (para que sea más fácil navegar entre entidades)
    componente = db.relationship('Producto', backref='movimientos', foreign_keys=[componente_id])
    responsable = db.relationship('Usuario', backref='movimientos_realizados', foreign_keys=[responsable_id])
    orden_servicio = db.relationship('OrdenServicio', backref='movimientos', foreign_keys=[orden_servicio_id])

# ✅ Modelo OrdenServicio
class OrdenServicio(db.Model):
    __tablename__ = 'ordenes_servicio'

    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.Text, nullable=True)
    estado = db.Column(db.String(20), default='pendiente')
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    def __repr__(self):
        return f'<OrdenServicio {self.id}>'
    
# ✅ Modelo Cotizacion
class Cotizacion(db.Model):
    __tablename__ = 'cotizaciones'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    componentes = db.Column(db.JSON, nullable=False)
    servicios = db.Column(db.JSON)
    total = db.Column(db.Integer, nullable=False)
    estado = db.Column(db.Enum('pendiente', 'aprobada', 'rechazada'), default='pendiente')
    validez_dias = db.Column(db.Integer, default=7)
    notas = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    cliente = db.relationship('Usuario', backref='cotizaciones')

    def __repr__(self):
        return f'<Cotizacion {self.codigo}>'
    
# ✅ Función para obtener la conexión a la base de datos 
def get_db():
    config = current_app.config
    return mysql.connector.connect(
        host=config['MYSQL_HOST'],
        user=config['MYSQL_USER'],
        password=config['MYSQL_PASSWORD'],
        database=config['MYSQL_DB'],
        port=config.get('MYSQL_PORT', 3306)
    )

# ✅ Modelo para las transacciones contables
class TransaccionContable(db.Model):
    __tablename__ = 'transacciones_contables'

    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    tipo = db.Column(db.Enum('ingreso', 'egreso'), nullable=False)
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    descripcion = db.Column(db.String(255))
    categoria = db.Column(db.String(100)) #Ejemplo: 'ventas', 'compras', 'gastos'
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    usuario = db.relationship('Usuario')

    def __repr__(self):
        return f'<TransaccionContable {self.id} {self.tipo} {self.monto}>'
    
# ✅ Modelo para las compras a proveedores
class Compra(db.Model):
    __tablename__ = 'compras'

    id = db.Column(db.Integer, primary_key=True)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    proveedor = db.relationship('Usuario', foreign_keys=[proveedor_id])
    producto = db.Column(db.String(100), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    usuario = db.relationship('Usuario', foreign_keys=[usuario_id])
    estado = db.Column(db.Enum('pendiente', 'aprobada', 'rechazada'), default='pendiente', nullable=False)

    def __repr__(self):
        return f'<Compra {self.id} {self.producto} x{self.cantidad}>'
    
# ✅ Modelo para los movimientos de stock
from app import db
from datetime import datetime

class MovimientoStock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('componentes.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # 'entrada' o 'salida'
    cantidad = db.Column(db.Integer, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    observacion = db.Column(db.String(255))

    producto = db.relationship('Producto', backref=db.backref('movimientos_stock', lazy=True))