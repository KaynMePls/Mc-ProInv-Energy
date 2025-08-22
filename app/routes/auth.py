from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
from app.models import Usuario
from app import db
from flask_login import login_user, logout_user


auth_bp = Blueprint('auth', __name__)


ROLES = {
    'admin': 'Administrador',
    'proveedor': 'Proveedor',
    'tecnico': 'Técnico',
    'inventario': 'Gestión de Inventario',
    'contabilidad': 'Contabilidad',
    'cliente': 'Cliente'
}

@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        telefono = request.form['telefono']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # rol fijo
        rol = 'cliente'

        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'danger')
            return redirect(url_for('auth.registro'))

        if len(password) < 8:
            flash('La contraseña debe tener al menos 8 caracteres', 'danger')
            return redirect(url_for('auth.registro'))

        if Usuario.query.filter_by(email=email).first():
            flash('Este correo ya está registrado', 'danger')
            return redirect(url_for('auth.registro'))

        nuevo_usuario = Usuario(
            nombre=nombre,
            email=email,
            telefono=telefono,
            password=generate_password_hash(password),
            rol='cliente',
            estado='activo'
        )

        try:
            db.session.add(nuevo_usuario)
            db.session.commit()
            flash('Registro exitoso. Ahora puedes iniciar sesión', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('Error al registrar: ' + str(e), 'danger')

    return render_template('auth/registro.html')



@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = Usuario.query.filter_by(email=email, estado='activo').first()

        if user and check_password_hash(user.password, password):
            login_user(user)  # ✅ Primero autenticas

            # Guarda solo lo necesario
            session['user_id'] = user.id
            session['user_rol'] = user.rol
            session['user_nombre'] = user.nombre

            # Redirección por rol
            if user.rol == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user.rol == 'cliente':
                return redirect(url_for('cliente.dashboard'))
            elif user.rol == 'proveedor':
                return redirect(url_for('proveedor.dashboard'))
            elif user.rol == 'inventario':
                return redirect(url_for('inventarios.dashboard'))
            elif user.rol == 'contabilidad':
                return redirect(url_for('contabilidad.dashboard'))

        flash('Credenciales incorrectas o cuenta inactiva', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    logout_user()
    flash('Sesión cerrada con éxito', 'info')
    return redirect(url_for('auth.login'))


