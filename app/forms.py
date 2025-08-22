from flask_wtf import FlaskForm
from wtforms import SelectField, DecimalField, DateTimeLocalField, TextAreaField, SubmitField, IntegerField, DateField, StringField
from wtforms.validators import DataRequired, Length, NumberRange

# Formulario para registrar transacciones contables
class TransaccionForm(FlaskForm):
    tipo = SelectField('Tipo de transacción', choices=[('ingreso', 'Ingreso'), ('egreso', 'Egreso')], validators=[DataRequired()])
    monto = DecimalField('Monto', places=2, validators=[DataRequired()])
    fecha = DateTimeLocalField('Fecha', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    categoria = SelectField('Categoría', choices=[], validators=[DataRequired()])
    descripcion = TextAreaField('Descripción', validators=[Length(max=200)])
    submit = SubmitField('Registrar')

# Formulario para registrar compras
class CompraForm(FlaskForm):
    proveedor = SelectField('Proveedor', validators=[DataRequired()], choices=[])
    producto = StringField('Producto', validators=[DataRequired()])
    cantidad = IntegerField('Cantidad', validators=[DataRequired(), NumberRange(min=1)])
    precio_unitario = DecimalField('Precio Unitario', validators=[DataRequired(), NumberRange(min=0)])
    fecha = DateField('Fecha de Compra', validators=[DataRequired()])
    submit = SubmitField('Guardar Compra')

# estado de compra
class EstadoCompraForm(FlaskForm):
    estado = SelectField('Estado', choices=[('pendiente', 'Pendiente'), ('aprobada', 'Aprobada'), ('rechazada', 'Rechazada')], validators=[DataRequired()])
    submit = SubmitField('Actualizar Estado')

# Formulario para registrar productos
class ProductoForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    descripcion = TextAreaField('Descripción')
    precio = DecimalField('Precio', validators=[DataRequired()])
    stock = IntegerField('Stock', validators=[DataRequired()])
    imagen_url = StringField('URL de Imagen')
    submit = SubmitField('Guardar')