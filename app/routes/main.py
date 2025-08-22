from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def inicio():
    return render_template('inicio.html')  # o un simple mensaje si no hay HTML
