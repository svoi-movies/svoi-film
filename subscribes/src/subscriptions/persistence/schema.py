import sqlalchemy as sa
from commons.outbox.sqlalchemy import create_outbox_table, map_outbox_table
from sqlalchemy.orm import registry

from subscriptions.domain.subscription import (
    Subscription,
    SubscriptionLevel,
    SubscriptionStatus,
)

# Registry with all SQLAlchemy mappings for the service
mapper_registry = registry()

outbox_table = create_outbox_table(mapper_registry.metadata, table_name="outbox")

subscription_level_enum = sa.Enum(SubscriptionLevel, name="subscriptionlevel")
subscription_status_enum = sa.Enum(SubscriptionStatus, name="subscriptionstatus")

subscriptions = sa.Table(
    "subscriptions",
    mapper_registry.metadata,
    sa.Column("id", sa.UUID(), primary_key=True),
    sa.Column("level", subscription_level_enum, nullable=False),
    sa.Column("status", subscription_status_enum, nullable=False),
    sa.Column("pending_level", subscription_level_enum, nullable=True),
    sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("level_change_initiated_at", sa.DateTime(timezone=True), nullable=True),
)


def wire_mappers() -> None:
    mapper_registry.map_imperatively(
        Subscription,
        subscriptions,
        properties={
            "_id": subscriptions.c.id,
            "_level": subscriptions.c.level,
            "_status": subscriptions.c.status,
            "_pending_level": subscriptions.c.pending_level,
            "_expires_at": subscriptions.c.expires_at,
            "_created_at": subscriptions.c.created_at,
            "_cancelled_at": subscriptions.c.cancelled_at,
            "_level_change_initiated_at": subscriptions.c.level_change_initiated_at,
        },
    )

    map_outbox_table(mapper_registry, outbox_table)
