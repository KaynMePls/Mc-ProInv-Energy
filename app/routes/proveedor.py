from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.models import Producto, Compra
from app.forms import ProductoForm
from app import db
import os
from werkzeug.utils import secure_filename
from flask import current_app
from app.models import Producto, Compra, MovimientoStock
from decimal import Decimal


proveedor_bp = Blueprint('proveedor', __name__, url_prefix='/proveedor')

# ruta para el dashboard del proveedor
@proveedor_bp.route('/dashboard')
@login_required
def dashboard():
    productos = Producto.query.filter_by(proveedor_id=current_user.id).all()
    ordenes = Compra.query.filter(Compra.proveedor.has(nombre=current_user.nombre)).order_by(Compra.fecha.desc()).all()
    ventas_recientes = sum([orden.precio_unitario * orden.cantidad for orden in ordenes]) if ordenes else 0
    return render_template(
        'proveedor/dashboard.html',
        productos=productos,
        ordenes=ordenes,
        ventas_recientes=ventas_recientes,
        Decimal=Decimal
    )
# ruta para crear un nuevo producto
@proveedor_bp.route('/producto/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_producto():
    form = ProductoForm()
    if form.validate_on_submit():
        imagen_archivo = request.files.get('imagen_archivo')
        imagen_url = form.imagen_url.data.strip()
        imagen_final = None

        if imagen_archivo and imagen_archivo.filename != '':
            filename = secure_filename(imagen_archivo.filename)
            ruta_upload = os.path.join(current_app.static_folder, 'img_productos', filename)
            os.makedirs(os.path.dirname(ruta_upload), exist_ok=True)
            imagen_archivo.save(ruta_upload)
            imagen_final = filename  # Solo el nombre
        elif imagen_url:
            imagen_final = imagen_url

        producto = Producto(
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            precio=form.precio.data,
            stock=form.stock.data,
            proveedor_id=current_user.id,
            imagen_url=imagen_final
        )
        db.session.add(producto)
        db.session.commit()
        flash('Producto creado exitosamente.', 'success')
        return redirect(url_for('proveedor.dashboard'))
    else:
        print(form.errors)  # Para depuración
    return render_template('proveedor/nuevo_producto.html', form=form)
# ruta para editar un producto
@proveedor_bp.route('/producto/editar/<int:producto_id>', methods=['GET', 'POST'])
@login_required
def editar_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    if producto.proveedor_id != current_user.id:
        flash('No tienes permiso para editar este producto.', 'danger')
        return redirect(url_for('proveedor.dashboard'))
    form = ProductoForm(obj=producto)
    if form.validate_on_submit():
        producto.nombre = form.nombre.data
        producto.descripcion = form.descripcion.data
        producto.precio = form.precio.data
        producto.stock = form.stock.data

        # Manejo de imagen: archivo o URL
        imagen_archivo = request.files.get('imagen_archivo')
        imagen_url = form.imagen_url.data.strip()

        if imagen_archivo and imagen_archivo.filename != '':
            filename = secure_filename(imagen_archivo.filename)
            ruta_upload = os.path.join(current_app.static_folder, 'uploads', filename)
            os.makedirs(os.path.dirname(ruta_upload), exist_ok=True)
            imagen_archivo.save(ruta_upload)
            producto.imagen_url = url_for('static', filename=f'uploads/{filename}')
        elif imagen_url:
            producto.imagen_url = imagen_url
        # Si no se envía nada, se mantiene la imagen actual

        db.session.commit()
        flash('Producto actualizado.', 'success')
        return redirect(url_for('proveedor.dashboard'))
    return render_template('proveedor/editar_producto.html', form=form, producto=producto)
# ruta para ver detalles de un producto
@proveedor_bp.route('/producto/<int:producto_id>')
@login_required
def detalle_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    if producto.proveedor_id != current_user.id:
        flash('No tienes permiso para ver este producto.', 'danger')
        return redirect(url_for('proveedor.dashboard'))
    return render_template('proveedor/detalle_producto.html', producto=producto)

#Ruta para ver las órdenes del proveedor
@proveedor_bp.route('/ordenes')
@login_required
def ordenes():
    ordenes = Compra.query.filter(Compra.proveedor.has(nombre=current_user.nombre)).order_by(Compra.fecha.desc()).all()
    return render_template('proveedor/ordenes.html', ordenes=ordenes)

# Ruta para ver detalles de una orden
@proveedor_bp.route('/orden/<int:orden_id>')
@login_required
def detalle_orden(orden_id):
    orden = Compra.query.get_or_404(orden_id)
    if orden.proveedor is None or orden.proveedor.nombre != current_user.nombre:
        flash('No tienes permiso para ver esta orden.', 'danger')
        return redirect(url_for('proveedor.ordenes'))
    return render_template('proveedor/detalle_orden.html', orden=orden)

# Ruta para ver historial de movimientos de stock de un producto
@proveedor_bp.route('/producto/<int:producto_id>/movimientos')
@login_required
def movimientos_stock(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    if producto.proveedor_id != current_user.id:
        flash('No tienes permiso para ver este producto.', 'danger')
        return redirect(url_for('proveedor.dashboard'))
    movimientos = MovimientoStock.query.filter_by(producto_id=producto_id).order_by(MovimientoStock.fecha.desc()).all()
    return render_template('proveedor/movimientos_stock.html', producto=producto, movimientos=movimientos)