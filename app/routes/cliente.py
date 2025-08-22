from flask import Blueprint, render_template, session, request, flash, url_for, redirect
from flask_login import login_required, current_user
from app.models import get_db, Producto, Servicio, CategoriaComponente, Cotizacion
from app import db
from app.utilities.carrito import procesar_checkout
from math import ceil
from datetime import datetime
import json
import random
from app.models import DetalleFactura, Factura, TransaccionContable
from flask import request, redirect, url_for, flash, session

cliente_bp = Blueprint('cliente', __name__, url_prefix='/cliente')
# Ruta para el dashboard del cliente
@cliente_bp.route('/dashboard')
@login_required
def dashboard():
    # Parámetros de paginación
    pagina_actual = int(request.args.get('page', 1))
    productos_por_pagina = 12

    # Filtros
    q = request.args.get('q', '')
    categoria = request.args.get('categoria', '')

    # Consulta base
    productos_query = Producto.query
    productos_query = productos_query.filter(Producto.stock > 0, Producto.estado == 'activo')
    if q:
        productos_query = productos_query.filter(Producto.nombre.ilike(f'%{q}%'))
    if categoria:
        productos_query = productos_query.filter(Producto.categoria_id == categoria)

    total_productos = productos_query.count()
    total_paginas = ceil(total_productos / productos_por_pagina)

    productos = productos_query.offset((pagina_actual - 1) * productos_por_pagina).limit(productos_por_pagina).all()
    servicios = Servicio.query.all()
    categorias = CategoriaComponente.query.all()

    # --- RESUMEN PARA DASHBOARD ---
    user_id = session.get('user_id')
    total_gastado = db.session.query(db.func.sum(Factura.total)).filter_by(cliente_id=user_id).scalar() or 0
    total_cotizaciones = Cotizacion.query.filter_by(cliente_id=user_id).count()
    total_compras = Factura.query.filter_by(cliente_id=user_id).count()
    servicios_activos = Servicio.query.filter_by(cliente_id=user_id, estado='activo').count() if hasattr(Servicio, 'cliente_id') else 0

    resumen = {
        'total_gastado': total_gastado,
        'total_cotizaciones': total_cotizaciones,
        'total_compras': total_compras,
        'servicios_activos': servicios_activos
    }

    # --- RESUMEN DEL CARRITO ---
    carrito = session.get('carrito', {})
    carrito_servicios = session.get('carrito_servicios', {})
    total_items = sum(carrito.values()) + sum(carrito_servicios.values())
    total_precio = 0

    if carrito:
        productos_db = Producto.query.filter(Producto.id.in_(carrito.keys())).all()
        for producto in productos_db:
            cantidad = carrito.get(str(producto.id), 0)
            total_precio += float(producto.precio) * cantidad
    if carrito_servicios:
        servicios_db = Servicio.query.filter(Servicio.id.in_(carrito_servicios.keys())).all()
        for servicio in servicios_db:
            cantidad = carrito_servicios.get(str(servicio.id), 0)
            total_precio += float(servicio.precio_base) * cantidad

    resumen_carrito = None
    if total_items > 0:
        resumen_carrito = {
            'total_items': total_items,
            'total_precio': int(total_precio)
        }

    # --- ÚLTIMAS COMPRAS Y COTIZACIONES ---
    ultimas_compras = Factura.query.filter_by(cliente_id=user_id).order_by(Factura.fecha_emision.desc()).limit(3).all()
    ultimas_cotizaciones = Cotizacion.query.filter_by(cliente_id=user_id).order_by(Cotizacion.fecha_creacion.desc()).limit(3).all()

  
    # --- NOTIFICACIONES ---
    notificaciones = "¡Aprovecha nuestras ofertas de julio! Solicita tu cotización antes del 31."

    # --- OFERTAS O PRODUCTOS DESTACADOS ---
    ofertas = [
        {"imagen_url": url_for('static', filename='Carrusel/APEX PRO.png'), "titulo": "¡Oferta especial!", "descripcion": "Descuento en Teclados Mecanicos."},
        {"imagen_url": url_for('static', filename='Carrusel/Torre Gamer.png'), "titulo": "¡Oferta especial!", "descripcion": "Descuento en Chasis Gamer."},
        {"imagen_url": url_for('static', filename='Carrusel/ASUS TUF.png'), "titulo": "¡Oferta especial!", "descripcion": "Descuento en Monitores 27 pulgadas."},
        {"imagen_url": url_for('static', filename='Carrusel/Logitech HERO.png'), "titulo": "¡Oferta especial!", "descripcion": "Descuento en Mouse Gamer."},
        {"imagen_url": url_for('static', filename='Carrusel/MSI-placa.png'), "titulo": "¡Oferta especial!", "descripcion": "Descuento en Board Ulima generacion."},
        {"imagen_url": url_for('static', filename='Carrusel/Mantenimiento.png'), "titulo": "Instalación gratis", "descripcion": "Servicios estrella."}
    ]

    # --- ESTADO DE PEDIDOS/SERVICIOS ---
    estados_pedidos = [
        {"descripcion": "Pedido #1234", "estado": "En proceso"},
        {"descripcion": "Servicio #5678", "estado": "Finalizado"}
    ]

    # --- VALORACIONES Y RESEÑAS ---
    valoraciones = [
        {"producto_nombre": "Teclado APEX PRO", "puntaje": 5, "comentario": "Excelente producto"},
        {"producto_nombre": "Instalacion Basica", "puntaje": 4, "comentario": "Muy buen servicio"}
    ]

    return render_template(
        'cliente/dashboard.html',
        productos=productos,
        servicios=servicios,
        categorias=categorias,
        total_paginas=total_paginas,
        pagina_actual=pagina_actual,
        resumen=resumen,
        resumen_carrito=resumen_carrito,
        ultimas_compras=ultimas_compras,
        ultimas_cotizaciones=ultimas_cotizaciones,
        notificaciones=notificaciones,
        ofertas=ofertas,
        estados_pedidos=estados_pedidos,
        valoraciones=valoraciones
    )

# Ruta para el perfil del cliente
@cliente_bp.route('/perfil')
@login_required
def perfil():
    # Aquí puedes cargar los datos del usuario y renderizar el template de perfil
    return render_template('cliente/perfil.html')

# Ruta para ver detalles de un producto y servicio 👌
@cliente_bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    carrito = session.get('carrito', {})
    carrito_servicios = session.get('carrito_servicios', {})
    if not carrito and not carrito_servicios:
        flash('El carrito está vacío.', 'warning')
        return redirect(url_for('cliente.ver_carrito'))

    try:
        productos_db = Producto.query.filter(Producto.id.in_(carrito.keys())).all() if carrito else []
        servicios_db = Servicio.query.filter(Servicio.id.in_(carrito_servicios.keys())).all() if carrito_servicios else []
        subtotal = 0

        factura = Factura(
            numero_factura=f'FAC-{datetime.now().year}-{random.randint(1000,9999)}',
            cliente_id=session.get('user_id'),
            subtotal=0,
            iva=0,
            total=0,
            metodo_pago='efectivo',
            fecha_emision=datetime.utcnow()
        )
        db.session.add(factura)
        db.session.flush()

        # Procesar productos
        for producto in productos_db:
            cantidad = carrito.get(str(producto.id), 0)
            if producto.stock is None or producto.stock < cantidad:
                flash(f"No hay suficiente stock para {producto.nombre}.", "danger")
                return redirect(url_for('cliente.ver_carrito'))
            producto.stock -= cantidad
            precio_unitario = float(producto.precio)
            subtotal += precio_unitario * cantidad

            detalle = DetalleFactura(
                factura_id=factura.id,
                componente_id=producto.id,
                servicio_id=None,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                subtotal=precio_unitario * cantidad
            )
            db.session.add(detalle)

        # Procesar servicios
        for servicio in servicios_db:
            cantidad = carrito_servicios.get(str(servicio.id), 0)
            precio_unitario = float(servicio.precio_base)
            subtotal += precio_unitario * cantidad

            detalle = DetalleFactura(
                factura_id=factura.id,
                componente_id=None,
                servicio_id=servicio.id,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                subtotal=precio_unitario * cantidad
            )
            db.session.add(detalle)

        
        

        iva = int(subtotal * 0.19)
        total = int(subtotal + iva)
        factura.subtotal = int(subtotal)
        factura.iva = iva
        factura.total = total

        # Transacción contable
        transaccion = TransaccionContable(
            tipo ='ingreso',
            monto=factura.total,
            descripcion=f'Compra Marketplace, factura {factura.numero_factura}',
            categoria='compra',
            usuario_id=current_user.id,
        )
        db.session.add(transaccion)
        db.session.commit()
        session['carrito'] = {}
        session['carrito_servicios'] = {}
        flash(f'Compra realizada con éxito. Factura: {factura.numero_factura}', 'success')
        return redirect(url_for('cliente.dashboard'))
    except Exception as e:
        print(f'Error en checkout: {e}')
        db.session.rollback()
        flash('Ocurrió un error al procesar el checkout.', 'danger')
        return redirect(url_for('cliente.ver_carrito'))

# Ruta para agregar un producto al carrito
@cliente_bp.route('/agregar-carrito', methods=['POST'])
@login_required
def agregar_carrito():
    producto_id = request.form.get('producto_id')
    if not producto_id:
        flash("ID de producto inválido", "danger")
        return redirect(url_for('cliente.dashboard'))

    carrito = session.get('carrito', {})
    carrito[producto_id] = carrito.get(producto_id, 0) + 1
    session['carrito'] = carrito
    flash("Producto agregado al carrito", "success")
    return redirect(url_for('cliente.dashboard'))

# Ruta para ver el carrito de compras

@cliente_bp.route('/ver-carrito')
@login_required
def ver_carrito():
    carrito = session.get('carrito', {})
    carrito_servicios = session.get('carrito_servicios', {})

    productos = []
    total = 0

    if carrito:
        productos_db = Producto.query.filter(Producto.id.in_(carrito.keys())).all()
        for producto in productos_db:
            cantidad = carrito.get(str(producto.id), 0)
            subtotal = float(producto.precio) * cantidad
            productos.append({
                'id': producto.id,
                'nombre': producto.nombre,
                'precio': producto.precio,
                'cantidad': cantidad,
                'subtotal': subtotal,
                'imagen_url': producto.imagen_url if hasattr(producto, 'imagen_url') else None
            })
            total += subtotal

    servicios = []
    if carrito_servicios:
        servicios_db = Servicio.query.filter(Servicio.id.in_(carrito_servicios.keys())).all()
        for servicio in servicios_db:
            cantidad = carrito_servicios.get(str(servicio.id), 0)
            subtotal = float(servicio.precio_base) * cantidad
            servicios.append({
                'id': servicio.id,
                'nombre': servicio.nombre,
                'precio': servicio.precio_base,
                'cantidad': cantidad,
                'subtotal': subtotal,
                'descripcion': servicio.descripcion
            })
            total += subtotal

    return render_template('cliente/ver_carrito.html', productos=productos, servicios=servicios, total=total)
# Ruta para quitar un producto del carrito
@cliente_bp.route('/quitar-producto-carrito', methods=['POST'])
@login_required
def quitar_producto_carrito():
    producto_id = request.form.get('producto_id')
    carrito = session.get('carrito', {})
    if producto_id in carrito:
        del carrito[producto_id]
        session['carrito'] = carrito
        flash("Producto eliminado del carrito", "info")
    return redirect(url_for('cliente.ver_carrito'))

# Ruta para agregar un servicio al carrito
@cliente_bp.route('/agregar-servicio-carrito', methods=['POST'])
@login_required
def agregar_servicio_carrito():
    servicio_id = request.form.get('servicio_id')
    if not servicio_id:
        flash("ID de servicio inválido", "danger")
        return redirect(url_for('cliente.dashboard'))

    carrito_servicios = session.get('carrito_servicios', {})
    # Guarda el ID como string
    carrito_servicios[str(servicio_id)] = carrito_servicios.get(str(servicio_id), 0) + 1
    session['carrito_servicios'] = carrito_servicios
    flash("Servicio agregado al carrito", "success")
    return redirect(url_for('cliente.dashboard'))

# Ruta para vaciar el carrito de compras
@cliente_bp.route('/vaciar-carrito', methods=['POST'])
@login_required
def vaciar_carrito():
    session.pop('carrito', None)
    flash("Carrito vaciado", "info")
    return redirect(url_for('cliente.ver_carrito'))

def generar_codigo_cotizacion():
    numero = random.randint(1000, 9999)
    return f'COT-{datetime.now().year}-{numero}'

# Ruta para solicitar una cotización
@cliente_bp.route('/solicitar-cotizacion', methods=['POST'])
@login_required
def solicitar_cotizacion():
    carrito = session.get('carrito', {})
    carrito_servicios = session.get('carrito_servicios', {})

    if not carrito and not carrito_servicios:
        flash('Tu carrito está vacío.', 'warning')
        return redirect(url_for('cliente.ver_carrito'))

    usuario_id = session.get('user_id')
    componentes = []
    total = 0

    # Agregar productos
    for producto_id, cantidad in carrito.items():
        producto = Producto.query.get(int(producto_id))
        if not producto:
            continue
        subtotal = float(producto.precio) * cantidad
        componentes.append({
            'tipo': 'producto',
            'id': producto.id,
            'nombre': producto.nombre,
            'precio': float(producto.precio),
            'cantidad': cantidad,
            'subtotal': subtotal
        })
        total += subtotal

    # Agregar servicios
    for servicio_id, cantidad in carrito_servicios.items():
        servicio = Servicio.query.get(int(servicio_id))
        if not servicio:
            continue
        subtotal = float(servicio.precio_base) * cantidad
        componentes.append({
            'tipo': 'servicio',
            'id': servicio.id,
            'nombre': servicio.nombre,
            'precio': float(servicio.precio_base),
            'cantidad': cantidad,
            'subtotal': subtotal,
            'descripcion': servicio.descripcion
        })
        total += subtotal

    cotizacion = Cotizacion(
        codigo=generar_codigo_cotizacion(),
        cliente_id=usuario_id,
        componentes=json.dumps(componentes),
        total=total,
        estado='pendiente',
        validez_dias=7,
        fecha_creacion=datetime.utcnow()
    )
    db.session.add(cotizacion)
    db.session.commit()

    session['carrito'] = {}
    session['carrito_servicios'] = {}
    flash('Cotización generada exitosamente.', 'success')
    return redirect(url_for('cliente.mis_cotizaciones'))

# Ruta para ver las cotizaciones del cliente
@cliente_bp.route('/mis-cotizaciones')
@login_required
def mis_cotizaciones():
    if session.get('user_rol') != 'cliente':
        return redirect(url_for('auth.login'))

    cotizaciones = Cotizacion.query.filter_by(cliente_id=session['user_id']).order_by(Cotizacion.fecha_creacion.desc()).all()
    return render_template('cliente/mis_cotizaciones.html', cotizaciones=cotizaciones)

# Ruta para ver los detalles de una cotización
@cliente_bp.route('/cotizacion/<int:id>')
@login_required
def ver_cotizacion(id):
    cotizacion = Cotizacion.query.get_or_404(id)

    if cotizacion.cliente_id != session.get('user_id'):
        flash("No tienes permiso para ver esta cotización.", "danger")
        return redirect(url_for('cliente.mis_cotizaciones'))

    return render_template('cliente/ver_cotizacion.html', cotizacion=cotizacion)

# Ruta para aceptar una cotización
@cliente_bp.route('/cotizaciones')
def cotizaciones():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    cliente_id = session.get('user_id')
    nombre_cliente = session.get('user_nombre')

    cotizaciones = Cotizacion.query.filter_by(cliente_id=cliente_id).order_by(Cotizacion.fecha_creacion.desc()).all()
    return render_template('cliente/cotizaciones.html', cotizaciones=cotizaciones, nombre_cliente=nombre_cliente)

# Ruta para ver el historial de compras del cliente
@cliente_bp.route('/historial-compras')
@login_required
def historial_compras():
    facturas = Factura.query.filter_by(cliente_id=session.get('user_id')).order_by(Factura.fecha_emision.desc()).all()
    return render_template('cliente/historial_compras.html', facturas=facturas)

# Ruta para ver los detalles de una factura
@cliente_bp.route('/factura/<int:id>')
@login_required
def ver_factura(id):
    factura = Factura.query.get_or_404(id)
    if factura.cliente_id != session.get('user_id'):
        flash("No tienes permiso para ver esta factura.", "danger")
        return redirect(url_for('cliente.historial_compras'))
    return render_template('cliente/ver_factura.html', factura=factura)

# Ruta para descargar una factura en PDF
from weasyprint import HTML
from io import BytesIO
from flask import make_response

@cliente_bp.route('/factura/<int:id>/pdf')
@login_required
def descargar_factura_pdf(id):
    factura = Factura.query.get_or_404(id)
    if factura.cliente_id != session.get('user_id'):
        flash("No tienes permiso para descargar esta factura.", "danger")
        return redirect(url_for('cliente.historial_compras'))
    html = render_template('cliente/ver_factura.html', factura=factura)
    pdf = HTML(string=html, base_url=request.base_url).write_pdf()
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=factura_{factura.numero_factura}.pdf'
    return response

# Ruta para quitar un servicio del carrito
@cliente_bp.route('/quitar-servicio-carrito', methods=['POST'])
@login_required
def quitar_servicio_carrito():
    servicio_id = request.form.get('servicio_id')
    carrito_servicios = session.get('carrito_servicios', {})
    if servicio_id and servicio_id in carrito_servicios:
        carrito_servicios.pop(servicio_id)
        session['carrito_servicios'] = carrito_servicios
        flash("Servicio eliminado del carrito", "success")
    else:
        flash("No se pudo eliminar el servicio", "danger")
    return redirect(url_for('cliente.ver_carrito'))

# Ruta par editar la cantidad de un producto en el carrito
@cliente_bp.route('/editar-cantidad-producto', methods=['POST'])
@login_required
def editar_cantidad_producto():
    producto_id = request.form.get('producto_id')
    cantidad = request.form.get('cantidad', type=int)
    carrito = session.get('carrito', {})
    if producto_id and cantidad and cantidad > 0:
        carrito[producto_id] = cantidad
        session['carrito'] = carrito
        flash('Cantidad actualizada.', 'success')
    else:
        flash('Cantidad inválida.', 'danger')
    return redirect(url_for('cliente.ver_carrito'))

# Ruta para editar la cantidad de un servicio en el carrito
@cliente_bp.route('/editar-cantidad-servicio', methods=['POST'])
@login_required
def editar_cantidad_servicio():
    servicio_id = request.form.get('servicio_id')
    cantidad = request.form.get('cantidad', type=int)
    carrito_servicios = session.get('carrito_servicios', {})
    if servicio_id and cantidad and cantidad > 0:
        carrito_servicios[servicio_id] = cantidad
        session['carrito_servicios'] = carrito_servicios
        flash('Cantidad actualizada.', 'success')
    else:
        flash('Cantidad inválida.', 'danger')
    return redirect(url_for('cliente.ver_carrito'))

# Ruta para ver los detalles de un producto
@cliente_bp.route('/producto/<int:id>')
@login_required
def ver_producto(id):
    producto = Producto.query.get_or_404(id)
    return render_template('cliente/producto.html', producto=producto)

