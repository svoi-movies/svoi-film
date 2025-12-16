from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from dishka import Provider, Scope, provide


class DbConfig(BaseModel):
    dsn: str
    expire_on_commit: bool


class SqlAlchemyProvider(Provider):

    @provide(scope=Scope.APP)
    async def engine(self, config: DbConfig) -> AsyncEngine:
        return create_async_engine(url=config.dsn)

    @provide(scope=Scope.REQUEST)
    async def session(self, engine: AsyncEngine, config: DbConfig) -> AsyncSession:
        return AsyncSession(
            bind=engine,
            expire_on_commit=config.expire_on_commit,
        )
