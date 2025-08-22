import re
from flask import flash

def validar_email(email):
    if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
        flash('Formato de correo electrónico inválido', 'danger')
        return False
    return True

def validar_telefono(telefono):
    if not re.match(r'^[0-9]{10,15}$', telefono):
        flash('Teléfono debe contener solo números (10-15 dígitos)', 'danger')
        return False
    return True