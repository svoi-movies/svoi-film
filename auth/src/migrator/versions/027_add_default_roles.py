"""add default roles

Revision ID: 027_add_default_roles
Revises: 026_add_root_user
Create Date: 2025-12-20

"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '027_add_default_roles'
down_revision: Union[str, Sequence[str], None] = '71ffc064e2e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add default roles: viewer, moderator, content-owner, admin."""

    # Получаем root role id для установки creator_role_id
    root_role_result = op.get_bind().execute(
        sa.text("SELECT id FROM roles WHERE name = 'root'")
    )
    root_role_id = root_role_result.scalar_one()

    # Создаем роль viewer (с самостоятельной регистрацией)
    viewer_role_id = uuid.uuid4()
    op.execute(
        sa.text(
            """
            INSERT INTO roles (id, name, allow_self_registration, creator_role_id)
            VALUES (:role_id, 'viewer', true, NULL)
            """
        ).bindparams(
            sa.bindparam("role_id", value=viewer_role_id, type_=sa.UUID)
        )
    )

    # Создаем роль admin (создается root'ом)
    admin_role_id = uuid.uuid4()
    op.execute(
        sa.text(
            """
            INSERT INTO roles (id, name, allow_self_registration, creator_role_id)
            VALUES (:role_id, 'admin', false, :creator_role_id)
            """
        ).bindparams(
            sa.bindparam("role_id", value=admin_role_id, type_=sa.UUID),
            sa.bindparam("creator_role_id", value=root_role_id, type_=sa.UUID)
        )
    )

    # Создаем роль moderator (создается admin'ом)
    moderator_role_id = uuid.uuid4()
    op.execute(
        sa.text(
            """
            INSERT INTO roles (id, name, allow_self_registration, creator_role_id)
            VALUES (:role_id, 'moderator', false, :creator_role_id)
            """
        ).bindparams(
            sa.bindparam("role_id", value=moderator_role_id, type_=sa.UUID),
            sa.bindparam("creator_role_id", value=admin_role_id, type_=sa.UUID)
        )
    )

    # Создаем роль content-owner (создается admin'ом)
    content_owner_role_id = uuid.uuid4()
    op.execute(
        sa.text(
            """
            INSERT INTO roles (id, name, allow_self_registration, creator_role_id)
            VALUES (:role_id, 'content-owner', false, :creator_role_id)
            """
        ).bindparams(
            sa.bindparam("role_id", value=content_owner_role_id, type_=sa.UUID),
            sa.bindparam("creator_role_id", value=admin_role_id, type_=sa.UUID)
        )
    )


def downgrade() -> None:
    """Remove default roles."""
    op.execute(
        sa.text(
            """
            DELETE FROM roles
            WHERE name IN ('viewer', 'admin', 'moderator', 'content-owner')
            """
        )
    )
