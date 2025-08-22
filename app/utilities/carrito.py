from app import db
from app.models import Producto, Factura, DetalleFactura, MovimientoInventario
from datetime import datetime
import random
import string

def generar_codigo_factura():
    return 'F' + ''.join(random.choices(string.digits, k=6))

def procesar_checkout(carrito, usuario_id):
    # Crear factura
    codigo = generar_codigo_factura()
    factura = Factura(
        codigo=codigo,
        fecha=datetime.utcnow(),
        cliente_id=usuario_id
    )
    db.session.add(factura)
    db.session.flush()  # para obtener el ID de la factura antes de commit

    for producto_id, cantidad in carrito.items():
        producto = Producto.query.get(int(producto_id))
        if not producto:
            continue

        # Verificar stock suficiente
        if producto.stock < cantidad:
            raise Exception(f'Stock insuficiente para el producto {producto.nombre}')

        subtotal = producto.precio * cantidad

        # Crear detalle de factura
        detalle = DetalleFactura(
            factura_id=factura.id,
            producto_id=producto.id,
            cantidad=cantidad,
            precio_unitario=producto.precio,
            subtotal=subtotal
        )
        db.session.add(detalle)

        # Actualizar stock
        producto.stock -= cantidad
        db.session.add(producto)

        # Crear movimiento de inventario
        movimiento = MovimientoInventario(
            componente_id=producto.id,
            tipo='salida',
            cantidad=cantidad,
            responsable_id=usuario_id,
            referencia=codigo,
            motivo=f'Venta registrada en factura {codigo}',
            fecha=datetime.utcnow()
        )
        db.session.add(movimiento)

    db.session.commit()
    return factura
