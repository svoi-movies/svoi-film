import sqlalchemy as sa
from commons.outbox.sqlalchemy import create_outbox_table, map_outbox_table
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import registry

from content_owner.domain.content_owner import ContentOwner, ContentOwnerStatus

# Registry with all SQLAlchemy mappings for the service
mapper_registry = registry()

outbox_table = create_outbox_table(mapper_registry.metadata, table_name="outbox")

content_owner_status_enum = sa.Enum(
    ContentOwnerStatus,
    name="contentownerstatus",
    values_callable=lambda enum: [e.value for e in enum],
)

content_owners = sa.Table(
    "content_owners",
    mapper_registry.metadata,
    sa.Column("id", sa.UUID(), primary_key=True),
    sa.Column("user_id", sa.UUID(), nullable=False),
    sa.Column("company_id", sa.UUID(), nullable=False),
    sa.Column("permissions", ARRAY(sa.String(), as_tuple=True), nullable=False),
    sa.Column("status", content_owner_status_enum, nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
)


def wire_mappers() -> None:
    mapper_registry.map_imperatively(
        ContentOwner,
        content_owners,
        properties={
            "_id": content_owners.c.id,
            "_user_id": content_owners.c.user_id,
            "_company_id": content_owners.c.company_id,
            "_permissions": content_owners.c.permissions,
            "_status": content_owners.c.status,
            "_created_at": content_owners.c.created_at,
            "_updated_at": content_owners.c.updated_at,
        },
    )

    map_outbox_table(mapper_registry, outbox_table)
