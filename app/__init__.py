from flask import Flask, session, redirect, url_for, request, has_request_context
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, current_user, login_required
from flask_wtf import CSRFProtect
import json

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
login_manager = LoginManager()
csrf = CSRFProtect()

# filtro para formatear millas
def miles(value):
    try:
        return "{:,}".format(int(float(value))).replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return value 

# filtro para convertir de JSON a dict
def from_json(value):
    return json.loads(value)

# Inicialización de la aplicación Flask

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    app.jinja_env.filters['miles'] = miles
    app.jinja_env.filters['from_json'] = from_json

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app.models import Usuario 

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    # Importación de blueprints
    from app.routes.auth import auth_bp
    from app.routes.cliente import cliente_bp
    from app.routes.admin import admin_bp
    from app.routes.main import main_bp
    from app.routes.proveedor import proveedor_bp
    from app.routes.contabilidad import contabilidad_bp
    from app.routes.inventarios import inventarios_bp

    # Registro de blueprints
    app.register_blueprint(auth_bp) 
    app.register_blueprint(cliente_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(proveedor_bp)
    app.register_blueprint(contabilidad_bp)
    app.register_blueprint(inventarios_bp)

    # Middleware para requerir login
    @app.before_request
    def requerir_login():
        if not has_request_context():
            return

        rutas_publicas = (
            'auth.login', 'auth.registro', 'auth.logout', 'static', 'main.inicio'
        )
        endpoint = request.endpoint or ''
        if any(endpoint.startswith(r) for r in rutas_publicas):
            return

        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
    

    return app