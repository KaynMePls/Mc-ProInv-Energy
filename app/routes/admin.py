from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Usuario, Producto, Compra
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    total_usuarios = Usuario.query.count()
    total_productos = Producto.query.count()
    total_ordenes = Compra.query.count()
    total_ventas = sum([orden.precio_unitario * orden.cantidad for orden in Compra.query.all()])
    return render_template(
        'admin/dashboard.html',
        total_usuarios=total_usuarios,
        total_productos=total_productos,
        total_ordenes=total_ordenes,
        total_ventas=total_ventas
    )