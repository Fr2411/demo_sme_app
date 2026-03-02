"""add ui postgres core tables/columns

Revision ID: 20261027_02
Revises: 20261027_01
Create Date: 2026-10-27 00:10:00.000000
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '20261027_02'
down_revision: str | None = '20261027_01'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS sales (
            id SERIAL PRIMARY KEY,
            client_id VARCHAR(100) NOT NULL,
            product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
            qty INTEGER NOT NULL,
            selling_price NUMERIC(12,2) NOT NULL,
            sale_date TIMESTAMPTZ NOT NULL DEFAULT now(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_sales_client_id ON sales (client_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_sales_product_id ON sales (product_id)")

    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS client_id VARCHAR(100) DEFAULT 'demo_client'")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT now()")
    op.execute("CREATE INDEX IF NOT EXISTS ix_products_client_id ON products (client_id)")

    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS client_id VARCHAR(100) DEFAULT 'demo_client'")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'employee'")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT now()")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_client_id ON users (client_id)")

    op.execute(
        """
        INSERT INTO users (username, email, password_hash, is_active, client_id, role)
        VALUES ('owner', 'owner@example.com', 'owner123', true, 'demo_client', 'owner')
        ON CONFLICT (username) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute('DROP TABLE IF EXISTS sales')
