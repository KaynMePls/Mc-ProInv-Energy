from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Usuario, Producto, Compra, MovimientoInventario, TransaccionContable
from app import db
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from collections import defaultdict
from flask import request

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Ruta para el dashboard del administrador
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    # Estadísticas rápidas
    total_usuarios = Usuario.query.count()
    total_productos = Producto.query.count()
    total_ordenes = Compra.query.count()

    # Ventas: suma de todas las compras
    ventas_query = Compra.query
    total_ventas = sum([orden.precio_unitario * orden.cantidad for orden in ventas_query.all()])

    # Compras: todas las compras
    total_compras = sum([orden.precio_unitario * orden.cantidad for orden in Compra.query.all()])

    # Últimos 7 días
    hoy = datetime.today().date()
    dias = [(hoy - timedelta(days=i)) for i in range(6, -1, -1)]

    compras_por_dia = []
    ventas_por_dia = []
    ingresos_por_dia = []
    egresos_por_dia = []

    for dia in dias:
        inicio = datetime.combine(dia, datetime.min.time())
        fin = datetime.combine(dia, datetime.max.time())

        # Compras por día (todas)
        compras = sum([
            orden.precio_unitario * orden.cantidad
            for orden in Compra.query.filter(Compra.fecha >= inicio, Compra.fecha <= fin).all()
        ])
        compras_por_dia.append(compras)

        # Ventas por día (todas)
        ventas = sum([
            orden.precio_unitario * orden.cantidad
            for orden in Compra.query
                .filter(
                    Compra.fecha >= inicio,
                    Compra.fecha <= fin
                ).all()
        ])
        ventas_por_dia.append(ventas)

        # Ingresos y egresos por día
        ingresos = sum([
            t.monto for t in TransaccionContable.query
            .filter(
                TransaccionContable.fecha >= inicio,
                TransaccionContable.fecha <= fin,
                TransaccionContable.tipo == 'ingreso'
            ).all()
        ])
        egresos = sum([
            t.monto for t in TransaccionContable.query
            .filter(
                TransaccionContable.fecha >= inicio,
                TransaccionContable.fecha <= fin,
                TransaccionContable.tipo == 'egreso'
            ).all()
        ])
        ingresos_por_dia.append(ingresos)
        egresos_por_dia.append(egresos)

    # Movimientos recientes de inventario (últimos 5)
    movimientos_inventario = MovimientoInventario.query.order_by(desc(MovimientoInventario.fecha)).limit(5).all()

    # Movimientos recientes de contabilidad (últimos 5)
    movimientos_contables = TransaccionContable.query.order_by(desc(TransaccionContable.fecha)).limit(5).all()

    # Gráfica de pastel: Ventas por producto (todas las compras)
    ventas_por_producto = defaultdict(float)
    for orden in Compra.query.all():
        ventas_por_producto[orden.producto] += float(orden.precio_unitario) * orden.cantidad

    labels_ventas = list(ventas_por_producto.keys())
    datos_ventas = list(ventas_por_producto.values())

    return render_template(
        'admin/dashboard.html',
        total_usuarios=total_usuarios,
        total_productos=total_productos,
        total_ordenes=total_ordenes,
        total_ventas=total_ventas,
        total_compras=total_compras,
        dias=[dia.strftime('%d/%m') for dia in dias],
        ventas_por_dia=ventas_por_dia,
        compras_por_dia=compras_por_dia,
        ingresos_por_dia=ingresos_por_dia,
        egresos_por_dia=egresos_por_dia,
        movimientos_inventario=movimientos_inventario,
        movimientos_contables=movimientos_contables,
        labels_ventas=labels_ventas,
        datos_ventas=datos_ventas
    )
# ------------------- Gestión de Usuarios -------------------

@admin_bp.route('/usuarios')
@login_required
def usuarios():
    usuarios = Usuario.query.all()
    return render_template('admin/usuarios.html', usuarios=usuarios)

@admin_bp.route('/usuarios/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_usuario():
    if request.method == 'POST':
        documento = request.form['documento']
        nombre = request.form['nombre']
        email = request.form['email']
        telefono = request.form['telefono']
        direccion = request.form['direccion']
        rol = request.form['rol']
        estado = request.form['estado']
        password = request.form['password']
        nuevo = Usuario(
            documento=documento,
            nombre=nombre,
            email=email,
            telefono=telefono,
            direccion=direccion,
            rol=rol,
            estado=estado
        )
        nuevo.set_password(password)
        db.session.add(nuevo)
        db.session.commit()
        flash('Usuario creado exitosamente.', 'success')
        return redirect(url_for('admin.usuarios'))
    return render_template('admin/nuevo_usuario.html')

@admin_bp.route('/usuarios/<int:usuario_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_usuario(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    if request.method == 'POST':
        usuario.nombre = request.form['nombre']
        usuario.email = request.form['email']
        usuario.telefono = request.form['telefono']
        usuario.direccion = request.form['direccion']
        usuario.rol = request.form['rol']
        usuario.estado = request.form['estado']
        password = request.form.get('password')
        if password:
            usuario.set_password(password)  # Esto genera el hash scrypt
        db.session.commit()
        flash('Usuario actualizado.', 'success')
        return redirect(url_for('admin.usuarios'))
    return render_template('admin/editar_usuario.html', usuario=usuario)
@admin_bp.route('/usuarios/<int:usuario_id>/eliminar', methods=['POST'])
@login_required
def eliminar_usuario(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    db.session.delete(usuario)
    db.session.commit()
    flash('Usuario eliminado.', 'success')
    return redirect(url_for('admin.usuarios'))

# ------------------- Gestión de Productos -------------------


@admin_bp.route('/productos')
@login_required
def productos():
    productos = Producto.query.all()
    return render_template('admin/productos.html', productos=productos)

@admin_bp.route('/productos/nuevo')
@login_required
def nuevo_producto():
    return redirect(url_for('inventarios.nuevo_producto', cancel_url=url_for('admin.productos')))

@admin_bp.route('/productos/<int:producto_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_producto(producto_id):
    return redirect(url_for('inventarios.editar_producto', producto_id=producto_id, cancel_url=url_for('admin.productos')))

@admin_bp.route('/productos/<int:producto_id>/eliminar', methods=['POST'])
@login_required
def eliminar_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    db.session.delete(producto)
    db.session.commit()
    flash('Producto eliminado.', 'success')
    return redirect(url_for('admin.productos'))
# ------------------- Gestión de Órdenes -------------------

@admin_bp.route('/ordenes')
@login_required
def ordenes():
    ordenes = Compra.query.all()
    return render_template('admin/ordenes.html', ordenes=ordenes)

@admin_bp.route('/ordenes/nueva')
@login_required
def nueva_orden():
    return redirect(url_for('contabilidad.nueva_compra', cancel_url=url_for('admin.dashboard')))

@admin_bp.route('/ordenes/<int:orden_id>')
@login_required
def detalle_orden(orden_id):
    obj = Compra.query.get(orden_id)
    tipo = 'orden'
    if not obj:
        obj = TransaccionContable.query.get_or_404(orden_id)
        tipo = 'transaccion'
    cancel_url = request.args.get('cancel_url') or url_for('admin.ordenes')
    return render_template('admin/detalle_orden.html', obj=obj, tipo=tipo, cancel_url=cancel_url)

@admin_bp.route('/ordenes/<int:orden_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_orden(orden_id):
    # Intenta buscar primero como Compra
    obj = Compra.query.get(orden_id)
    tipo = 'orden'
    if not obj:
        obj = TransaccionContable.query.get_or_404(orden_id)
        tipo = 'transaccion'

    cancel_url = request.args.get('cancel_url') or url_for('admin.ordenes')

    if request.method == 'POST':
        # Solo permite editar ciertos campos para Compra
        if tipo == 'orden':
            cantidad = request.form.get('cantidad', type=int)
            precio_unitario = request.form.get('precio_unitario', type=float)
            estado = request.form.get('estado')
            descripcion = request.form.get('descripcion')

            if cantidad is not None:
                obj.cantidad = cantidad
            if precio_unitario is not None:
                obj.precio_unitario = precio_unitario
            if estado:
                obj.estado = estado
            obj.descripcion = descripcion

            db.session.commit()
            flash('Orden actualizada exitosamente.', 'success')
            return redirect(cancel_url)
        else:
            # Si es transacción, podrías redirigir a la edición de transacción
            return redirect(url_for('contabilidad.editar_transaccion', transaccion_id=orden_id, cancel_url=cancel_url))

    return render_template('admin/editar_orden.html', obj=obj, tipo=tipo, cancel_url=cancel_url)
@admin_bp.route('/ordenes/<int:orden_id>/eliminar', methods=['POST'])
@login_required
def eliminar_orden(orden_id):
    obj = Compra.query.get(orden_id)
    if not obj:
        obj = TransaccionContable.query.get_or_404(orden_id)
    db.session.delete(obj)
    db.session.commit()
    flash('Registro eliminado.', 'success')
    return redirect(url_for('admin.ordenes'))