"""Agrega relaciones en DetalleFactura

Revision ID: aef92a05179e
Revises: 
Create Date: 2025-07-22 22:43:15.249160

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'aef92a05179e'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('detalle_factura', schema=None) as batch_op:
        batch_op.alter_column('componente_id', 
                              existing_type=sa.Integer(), 
                              nullable=True)
        batch_op.alter_column('servicio_id', 
                              existing_type=sa.Integer(), 
                              nullable=True)