import sqlalchemy as sa
from commons.outbox.sqlalchemy import create_outbox_table, map_outbox_table
from sqlalchemy.orm import registry, relationship

from auth.domain.user import Session, User
from auth.domain.value_objects import Email

"""
Тут я положил вообще все, что связано маппингом алхимии.
"""


"""
В mapper_registry лежит вся инфа про то, какие таблички есть и как их смаппить в объекты
"""
mapper_registry = registry()

outbox_table = create_outbox_table(mapper_registry.metadata, table_name="outbox")


class EmailType(sa.TypeDecorator[Email]):
    """
    Это маппер для кастомных типов. Его придётся писать для каждого кастомного ValueObject.
    process_bind_param маппит из объекта в примитивный тип,
    process_result_value наоборот
    """

    impl = sa.String(64)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return value.value if value is not None else None

    def process_result_value(self, value, dialect):
        return None if value is None else Email(value)


"""
Это описание таблиц в БД
"""

users = sa.Table(
    "users",
    mapper_registry.metadata,
    sa.Column("id", sa.UUID(), primary_key=True),
    sa.Column("email", EmailType(), nullable=False, unique=True),
    sa.Column("first_name", sa.String(32), nullable=False),
    sa.Column("last_name", sa.String(32), nullable=False),
    sa.Column("status", sa.String(16), nullable=False),
    sa.Column("role", sa.String(16), nullable=False),
    sa.Column("password_hash", sa.String(64), nullable=False),
    sa.Column("email_verified", sa.Boolean(), nullable=False, default=False),
    sa.Column("must_reset_password", sa.Boolean(), nullable=False, default=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
)

sessions = sa.Table(
    "sessions",
    mapper_registry.metadata,
    sa.Column("id", sa.UUID(), primary_key=True),
    sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
)


def wire_mappers() -> None:
    """
    Маппит наши объекты на таблички
    """
    mapper_registry.map_imperatively(
        Session,
        sessions,
        properties={
            "_id": sessions.c.id,
            "_user_id": sessions.c.user_id,
            "_created_at": sessions.c.created_at,
            "_expires_at": sessions.c.expires_at,
            "_closed_at": sessions.c.closed_at,
        },
    )

    mapper_registry.map_imperatively(
        User,
        users,
        properties={
            "_id": users.c.id,
            "_email": users.c.email,
            "_first_name": users.c.first_name,
            "_last_name": users.c.last_name,
            "_status": users.c.status,
            "_role": users.c.role,
            "_password_hash": users.c.password_hash,
            "_email_verified": users.c.email_verified,
            "_must_reset_password": users.c.must_reset_password,
            "_created_at": users.c.created_at,
            "_sessions": relationship(
                Session,
                foreign_keys=[sessions.c.user_id],
                primaryjoin=users.c.id == sessions.c.user_id,
            ),
        },
    )

    map_outbox_table(mapper_registry, outbox_table)
