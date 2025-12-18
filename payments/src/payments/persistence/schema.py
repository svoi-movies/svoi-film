import sqlalchemy as sa
from commons.outbox.sqlalchemy import create_outbox_table, map_outbox_table
from sqlalchemy.orm import registry

from payments.domain.payment import Payment, PaymentStatus

# Registry with all SQLAlchemy mappings for the service
mapper_registry = registry()

outbox_table = create_outbox_table(mapper_registry.metadata, table_name="outbox")

payments = sa.Table(
    "payments",
    mapper_registry.metadata,
    sa.Column("id", sa.UUID(), primary_key=True),
    sa.Column("amount", sa.Numeric(12, 2), nullable=False),
    sa.Column("currency", sa.String(8), nullable=False),
    sa.Column("description", sa.Text(), nullable=True),
    sa.Column("status", sa.Enum(PaymentStatus), nullable=False),
    sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("succeeded_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("expired_at", sa.DateTime(timezone=True), nullable=True),
)


def wire_mappers() -> None:
    mapper_registry.map_imperatively(
        Payment,
        payments,
        properties={
            "_id": payments.c.id,
            "_amount": payments.c.amount,
            "_currency": payments.c.currency,
            "_description": payments.c.description,
            "_status": payments.c.status,
            "_expires_at": payments.c.expires_at,
            "_created_at": payments.c.created_at,
            "_succeeded_at": payments.c.succeeded_at,
            "_expired_at": payments.c.expired_at,
        },
    )

    map_outbox_table(mapper_registry, outbox_table)
