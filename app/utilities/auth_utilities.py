from werkzeug.security import generate_password_hash, check_password_hash
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import get_db
from functools import wraps

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, nombre, password, rol 
            FROM usuarios 
            WHERE email = %s AND estado = 'activo'
        """, (email,))
        user = cursor.fetchone()
        
        if user and check_password_hash(user['password'], password):
            session.clear()
            session['user_id'] = user['id']
            session['user_rol'] = user['rol']
            session['user_nombre'] = user['nombre']
            
            # Redirección por rol
            if user['rol'] == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user['rol'] == 'cliente':
                return redirect(url_for('cliente.dashboard'))  # corregido aquí también
            elif user['rol'] == 'proveedor':
                return redirect(url_for('proveedor.dashboard'))
            elif user['rol'] == 'inventario':
                return redirect(url_for('inventario.dashboard'))
            elif user['rol'] == 'contabilidad':
                return redirect(url_for('contabilidad.dashboard'))
            
        flash('Credenciales incorrectas o cuenta inactiva', 'danger')
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        telefono = request.form['telefono']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'danger')
            return redirect(url_for('auth.registro'))
        
        if len(password) < 8:
            flash('La contraseña debe tener al menos 8 caracteres', 'danger')
            return redirect(url_for('auth.registro'))
        
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        try:
            cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
            if cursor.fetchone():
                flash('Este correo ya está registrado', 'danger')
                return redirect(url_for('auth.registro'))
            
            cursor.execute("""
                INSERT INTO usuarios 
                (nombre, email, telefono, password, rol) 
                VALUES (%s, %s, %s, %s, 'cliente')
            """, (
                nombre,
                email,
                telefono,
                generate_password_hash(password)
            ))
            db.commit()
            
            flash('Registro exitoso. Ahora puedes iniciar sesión', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.rollback()
            flash('Error al registrar: ' + str(e), 'danger')
    
    return render_template('auth/registro.html')


def rol_requerido(*roles_permitidos):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_rol' not in session:
                flash('Debe iniciar sesión primero', 'warning')
                return redirect(url_for('auth.login'))
            
            if session['user_rol'] not in roles_permitidos:
                flash('No tiene permisos para acceder a esta sección', 'danger')
                return redirect(url_for('dashboard.index'))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator
