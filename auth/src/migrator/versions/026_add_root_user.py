"""add root user

Revision ID: 026_add_root_user
Revises: 025576389ff2
Create Date: 2025-12-20

"""
from typing import Sequence, Union
from datetime import datetime, timezone
import uuid

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '026_add_root_user'
down_revision: Union[str, Sequence[str], None] = '025576389ff2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add root role and root user."""
    # Создаем роль root
    root_role_id = uuid.uuid4()
    op.execute(
        sa.text(
            """
            INSERT INTO roles (id, name, allow_self_registration, creator_role_id)
            VALUES (:role_id, 'root', false, NULL)
            """
        ).bindparams(
            sa.bindparam("role_id", value=root_role_id, type_=sa.UUID)
        )
    )

    # Создаем пользователя root
    root_user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    op.execute(
        sa.text(
            """
            INSERT INTO users (
                id, email, role_id, first_name, last_name,
                status, password_hash, password_changed_at,
                created_by, email_verified_at, created_at
            )
            VALUES (
                :user_id, :email, :role_id, :first_name, :last_name,
                :status, :password_hash, :password_changed_at,
                :created_by, :email_verified_at, :created_at
            )
            """
        ).bindparams(
            sa.bindparam("user_id", value=root_user_id, type_=sa.UUID),
            sa.bindparam("email", value='root@svoifilm.com', type_=sa.String),
            sa.bindparam("role_id", value=root_role_id, type_=sa.UUID),
            sa.bindparam("first_name", value='root', type_=sa.String),
            sa.bindparam("last_name", value='root', type_=sa.String),
            sa.bindparam("status", value='active', type_=sa.String),
            sa.bindparam("password_hash", value='24326224313224435146567874583548453865326c464844357856664f62794939755452694a6d63377730386e784939586a516c6267516942374d47', type_=sa.String),
            sa.bindparam("password_changed_at", value=now, type_=sa.DateTime(timezone=True)),
            sa.bindparam("created_by", value=None, type_=sa.UUID),
            sa.bindparam("email_verified_at", value=now, type_=sa.DateTime(timezone=True)),
            sa.bindparam("created_at", value=now, type_=sa.DateTime(timezone=True)),
        )
    )


def downgrade() -> None:
    """Remove root user and role."""
    # Удаляем пользователя root
    op.execute(
        sa.text("DELETE FROM users WHERE email = 'root@svoifilm.com'")
    )

    # Удаляем роль root
    op.execute(
        sa.text("DELETE FROM roles WHERE name = 'root'")
    )
