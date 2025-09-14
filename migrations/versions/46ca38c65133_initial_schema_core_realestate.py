"""initial schema (core + realestate)

Revision ID: 46ca38c65133
Revises: 
Create Date: 2025-09-14 22:50:36.856048

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '46ca38c65133'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remover tabelas antigas do domínio de pizzaria com dependências primeiro (CASCADE)
    try:
        op.execute("DROP TABLE IF EXISTS order_items CASCADE")
        op.execute("DROP TABLE IF EXISTS order_status_events CASCADE")
        op.execute("DROP TABLE IF EXISTS order_relations CASCADE")
        op.execute("DROP TABLE IF EXISTS delivery_zones CASCADE")
        op.execute("DROP TABLE IF EXISTS store_hours CASCADE")
        op.execute("DROP TABLE IF EXISTS menu_items CASCADE")
        op.execute("DROP TABLE IF EXISTS customers CASCADE")
        op.execute("DROP TABLE IF EXISTS orders CASCADE")
    except Exception:
        pass
    """Upgrade schema."""
    # Nada adicional a executar; os DROPs acima já garantem limpeza do legado.
    pass


def downgrade() -> None:
    # No-op: não restauraremos o domínio antigo
    pass
