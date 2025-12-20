import sqlalchemy as sa
from commons.ddd.aggregate import Aggregate
from commons.outbox.sqlalchemy import create_outbox_table, map_outbox_table
from sqlalchemy import event
from sqlalchemy.orm import registry

from auth.domain.role import Role, Session, User, VerificationCode
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

roles = sa.Table(
    "roles",
    mapper_registry.metadata,
    sa.Column("id", sa.UUID(), primary_key=True),
    sa.Column("name", sa.String(64), nullable=False, unique=True),
    sa.Column("allow_self_registration", sa.Boolean(), nullable=False, default=False),
    sa.Column("creator_role_id", sa.UUID(), sa.ForeignKey("roles.id"), nullable=True),
)

users = sa.Table(
    "users",
    mapper_registry.metadata,
    sa.Column("id", sa.UUID(), primary_key=True),
    sa.Column("email", EmailType(), nullable=False, unique=True),
    sa.Column("role_id", sa.UUID(), sa.ForeignKey("roles.id"), nullable=False),
    sa.Column("first_name", sa.String(32), nullable=False),
    sa.Column("last_name", sa.String(32), nullable=False),
    sa.Column("status", sa.String(16), nullable=False),
    sa.Column("password_hash", sa.String(64), nullable=False),
    sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("created_by", sa.UUID(), sa.ForeignKey("users.id"), nullable=True),
    sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
)

verification_codes = sa.Table(
    "verification_codes",
    mapper_registry.metadata,
    sa.Column("id", sa.UUID(), primary_key=True),
    sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
    sa.Column("code", sa.String(7), nullable=False),
    sa.Column("valid_until", sa.DateTime(timezone=True), nullable=False),
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
        Role,
        roles,
        properties={
            "_id": roles.c.id,
            "name": roles.c.name,
            "allow_self_registration": roles.c.allow_self_registration,
            "creator_role_id": roles.c.creator_role_id,
        },
    )

    mapper_registry.map_imperatively(
        VerificationCode,
        verification_codes,
        properties={
            "_id": verification_codes.c.id,
            "user_id": verification_codes.c.user_id,
            "code": verification_codes.c.code,
            "valid_until": verification_codes.c.valid_until,
            "created_at": verification_codes.c.created_at,
        },
    )

    mapper_registry.map_imperatively(
        Session,
        sessions,
        properties={
            "_id": sessions.c.id,
            "user_id": sessions.c.user_id,
            "created_at": sessions.c.created_at,
            "expires_at": sessions.c.expires_at,
            "closed_at": sessions.c.closed_at,
        },
    )

    mapper_registry.map_imperatively(
        User,
        users,
        properties={
            "_id": users.c.id,
            "email": users.c.email,
            "role_id": users.c.role_id,
            "first_name": users.c.first_name,
            "last_name": users.c.last_name,
            "status": users.c.status,
            "password_hash": users.c.password_hash,
            "password_changed_at": users.c.password_changed_at,
            "created_by": users.c.created_by,
            "email_verified_at": users.c.email_verified_at,
            "created_at": users.c.created_at,
        },
    )

    map_outbox_table(mapper_registry, outbox_table)

    # Инициализируем агрегаты при загрузке из БД
    @event.listens_for(User, "load")
    def init_user(target, context):
        Aggregate.__init__(target, target._id)

    @event.listens_for(Role, "load")
    def init_role(target, context):
        Aggregate.__init__(target, target._id)

    @event.listens_for(Session, "load")
    def init_session(target, context):
        Aggregate.__init__(target, target._id)

    @event.listens_for(VerificationCode, "load")
    def init_verification_code(target, context):
        Aggregate.__init__(target, target._id)
