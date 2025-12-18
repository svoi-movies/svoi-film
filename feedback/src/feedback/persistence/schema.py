import sqlalchemy as sa
from commons.outbox.sqlalchemy import create_outbox_table, map_outbox_table
from sqlalchemy.orm import registry

from feedback.domain.models import Feedback, FeedbackEstimation, Title, TitleScore

mapper_registry = registry()

outbox_table = create_outbox_table(mapper_registry.metadata, table_name="outbox")

titles = sa.Table(
    "titles",
    mapper_registry.metadata,
    sa.Column("id", sa.UUID(), primary_key=True),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
)

title_scores = sa.Table(
    "title_scores",
    mapper_registry.metadata,
    sa.Column("id", sa.UUID(), primary_key=True),
    sa.Column("user_id", sa.UUID(), nullable=False),
    sa.Column("title_id", sa.UUID(), nullable=False),
    sa.Column("score", sa.Integer(), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    sa.UniqueConstraint("user_id", "title_id", name="uq_user_title_score"),
)

feedbacks = sa.Table(
    "feedbacks",
    mapper_registry.metadata,
    sa.Column("id", sa.UUID(), primary_key=True),
    sa.Column("user_id", sa.UUID(), nullable=False),
    sa.Column("title_id", sa.UUID(), nullable=False),
    sa.Column("text", sa.Text(), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
)

feedback_estimations = sa.Table(
    "feedback_estimations",
    mapper_registry.metadata,
    sa.Column("id", sa.UUID(), primary_key=True),
    sa.Column("user_id", sa.UUID(), nullable=False),
    sa.Column("feedback_id", sa.UUID(), sa.ForeignKey("feedbacks.id"), nullable=False),
    sa.Column("is_positive", sa.Boolean(), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    sa.UniqueConstraint("user_id", "feedback_id", name="uq_user_feedback_estimation"),
)


def wire_mappers() -> None:
    mapper_registry.map_imperatively(
        Title,
        titles,
        properties={
            "_id": titles.c.id,
            "created_at": titles.c.created_at,
        },
    )

    mapper_registry.map_imperatively(
        TitleScore,
        title_scores,
        properties={
            "_id": title_scores.c.id,
            "user_id": title_scores.c.user_id,
            "title_id": title_scores.c.title_id,
            "score": title_scores.c.score,
            "created_at": title_scores.c.created_at,
            "updated_at": title_scores.c.updated_at,
        },
    )

    mapper_registry.map_imperatively(
        Feedback,
        feedbacks,
        properties={
            "_id": feedbacks.c.id,
            "user_id": feedbacks.c.user_id,
            "title_id": feedbacks.c.title_id,
            "text": feedbacks.c.text,
            "created_at": feedbacks.c.created_at,
            "updated_at": feedbacks.c.updated_at,
        },
    )

    mapper_registry.map_imperatively(
        FeedbackEstimation,
        feedback_estimations,
        properties={
            "_id": feedback_estimations.c.id,
            "user_id": feedback_estimations.c.user_id,
            "feedback_id": feedback_estimations.c.feedback_id,
            "is_positive": feedback_estimations.c.is_positive,
            "created_at": feedback_estimations.c.created_at,
            "updated_at": feedback_estimations.c.updated_at,
        },
    )

    map_outbox_table(mapper_registry, outbox_table)
