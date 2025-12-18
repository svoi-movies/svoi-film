import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import sqlalchemy as sa
from aio_pika import ExchangeType
from aio_pika.abc import AbstractConnection
from dishka import AsyncContainer
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy.ext.asyncio import AsyncEngine

from feedback.config import Config
from feedback.container import create_container
from feedback.persistence.schema import wire_mappers

instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_respect_env_var=False,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/metrics"],
    inprogress_name="inprogress",
    inprogress_labels=True,
)

logger = logging.getLogger(__name__)


def create_base_app() -> FastAPI:
    from .routes import router

    app = FastAPI(lifespan=lifespan)
    app.include_router(router)
    instrumentator.instrument(app).expose(app)

    return app


def create_app() -> FastAPI:
    app = create_base_app()

    container = create_container()
    setup_dishka(container, app)
    wire_mappers()

    return app


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    container: AsyncContainer = app.state.dishka_container
    _ = await container.get(Config)
    await check_db_connection(container)
    yield


async def check_db_connection(container: AsyncContainer) -> None:
    engine = await container.get(AsyncEngine)
    async with engine.connect() as conn:
        await conn.scalar(sa.select(1))
    logger.info("Successfully connected to database")
