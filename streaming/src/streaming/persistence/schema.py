import sqlalchemy as sa
from commons.outbox.sqlalchemy import create_outbox_table, map_outbox_table
from sqlalchemy.orm import registry

from streaming.domain.viewer import Viewer
from streaming.domain.title import Title
from streaming.domain.episode import Episode, EpisodeStatus
from streaming.domain.viewing_session import ViewingSession

# Registry with all SQLAlchemy mappings for the service
mapper_registry = registry()

outbox_table = create_outbox_table(mapper_registry.metadata, table_name="outbox")

viewers = sa.Table(
    "viewers",
    mapper_registry.metadata,
    sa.Column("id", sa.UUID(), primary_key=True),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
)

titles = sa.Table(
    "titles",
    mapper_registry.metadata,
    sa.Column("id", sa.UUID(), primary_key=True),
    sa.Column("name", sa.Text(), nullable=False),
    sa.Column("description", sa.Text(), nullable=True),
    sa.Column("director", sa.Text(), nullable=True),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
)

episodes = sa.Table(
    "episodes",
    mapper_registry.metadata,
    sa.Column("id", sa.UUID(), primary_key=True),
    sa.Column("title_id", sa.UUID(), sa.ForeignKey("titles.id"), nullable=False),
    sa.Column("s3_key", sa.Text(), nullable=False),
    sa.Column("name", sa.Text(), nullable=False),
    sa.Column("description", sa.Text(), nullable=True),
    sa.Column("duration", sa.Integer(), nullable=True),
    sa.Column("status", sa.Enum(EpisodeStatus), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("hidden_at", sa.DateTime(timezone=True), nullable=True),
)

viewing_sessions = sa.Table(
    "viewing_sessions",
    mapper_registry.metadata,
    sa.Column("id", sa.UUID(), primary_key=True),
    sa.Column("viewer_id", sa.UUID(), sa.ForeignKey("viewers.id"), nullable=False),
    sa.Column("episode_id", sa.UUID(), sa.ForeignKey("episodes.id"), nullable=False),
    sa.Column("progress_seconds", sa.Integer(), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
)


def wire_mappers() -> None:
    mapper_registry.map_imperatively(
        Viewer,
        viewers,
        properties={
            "_id": viewers.c.id,
            "_created_at": viewers.c.created_at,
            "_deleted_at": viewers.c.deleted_at,
        },
    )

    mapper_registry.map_imperatively(
        Title,
        titles,
        properties={
            "_id": titles.c.id,
            "_name": titles.c.name,
            "_description": titles.c.description,
            "_director": titles.c.director,
            "_created_at": titles.c.created_at,
        },
    )

    mapper_registry.map_imperatively(
        Episode,
        episodes,
        properties={
            "_id": episodes.c.id,
            "_title_id": episodes.c.title_id,
            "_s3_key": episodes.c.s3_key,
            "_name": episodes.c.name,
            "_description": episodes.c.description,
            "_duration": episodes.c.duration,
            "_status": episodes.c.status,
            "_created_at": episodes.c.created_at,
            "_uploaded_at": episodes.c.uploaded_at,
            "_processed_at": episodes.c.processed_at,
            "_published_at": episodes.c.published_at,
            "_hidden_at": episodes.c.hidden_at,
        },
    )

    mapper_registry.map_imperatively(
        ViewingSession,
        viewing_sessions,
        properties={
            "_id": viewing_sessions.c.id,
            "_viewer_id": viewing_sessions.c.viewer_id,
            "_episode_id": viewing_sessions.c.episode_id,
            "_progress_seconds": viewing_sessions.c.progress_seconds,
            "_created_at": viewing_sessions.c.created_at,
            "_completed_at": viewing_sessions.c.completed_at,
        },
    )

    map_outbox_table(mapper_registry, outbox_table)
