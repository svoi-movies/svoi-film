import sqlalchemy as sa
from commons.outbox.sqlalchemy import create_outbox_table, map_outbox_table
from sqlalchemy.orm import registry

from moderator.domain.moderation_request import (
    ModerationRequest,
    ModerationRequestStatus,
)
from moderator.domain.moderator import Moderator, ModeratorStatus

# Registry with all SQLAlchemy mappings for the service
mapper_registry = registry()

outbox_table = create_outbox_table(mapper_registry.metadata, table_name="outbox")

moderator_status_enum = sa.Enum(
    ModeratorStatus,
    name="moderatorstatus",
    values_callable=lambda enum: [e.value for e in enum],
)

moderation_request_status_enum = sa.Enum(
    ModerationRequestStatus,
    name="moderationrequeststatus",
    values_callable=lambda enum: [e.value for e in enum],
)

moderators = sa.Table(
    "moderators",
    mapper_registry.metadata,
    sa.Column("id", sa.UUID(), primary_key=True),
    sa.Column("user_id", sa.UUID(), nullable=False),
    sa.Column("status", moderator_status_enum, nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
)

moderation_requests = sa.Table(
    "moderation_requests",
    mapper_registry.metadata,
    sa.Column("id", sa.UUID(), primary_key=True),
    sa.Column("episode_id", sa.UUID(), nullable=False),
    sa.Column("content_owner_id", sa.UUID(), nullable=False),
    sa.Column("moderator_id", sa.UUID(), nullable=True),
    sa.Column("status", moderation_request_status_enum, nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
)


def wire_mappers() -> None:
    mapper_registry.map_imperatively(
        Moderator,
        moderators,
        properties={
            "_id": moderators.c.id,
            "_user_id": moderators.c.user_id,
            "_status": moderators.c.status,
            "_created_at": moderators.c.created_at,
            "_updated_at": moderators.c.updated_at,
        },
    )

    mapper_registry.map_imperatively(
        ModerationRequest,
        moderation_requests,
        properties={
            "_id": moderation_requests.c.id,
            "_episode_id": moderation_requests.c.episode_id,
            "_content_owner_id": moderation_requests.c.content_owner_id,
            "_moderator_id": moderation_requests.c.moderator_id,
            "_status": moderation_requests.c.status,
            "_created_at": moderation_requests.c.created_at,
            "_updated_at": moderation_requests.c.updated_at,
        },
    )

    map_outbox_table(mapper_registry, outbox_table)
