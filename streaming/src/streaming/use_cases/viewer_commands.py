from datetime import datetime
from uuid import UUID

from commons.utils.common_providers import DateTimeProvider, UUIDProvider

from streaming.domain.viewer import Viewer
from streaming.persistence.uow import StreamingUnitOfWork


class ViewerCommands:
    def __init__(
        self,
        uow: StreamingUnitOfWork,
        datetime_provider: DateTimeProvider,
        uuid_provider: UUIDProvider,
    ) -> None:
        self._uow = uow
        self._datetime_provider = datetime_provider
        self._uuid_provider = uuid_provider

    async def create_viewer(self) -> Viewer:
        now = self._datetime_provider.now_utc
        viewer = Viewer.new(
            viewer_id=self._uuid_provider.new_v4(),
            now=now,
        )
        async with self._uow:
            self._uow.viewers.add(viewer)
            await self._uow.commit()
        return viewer

    async def delete_viewer(self, viewer_id: UUID) -> Viewer:
        now = self._datetime_provider.now_utc
        async with self._uow:
            viewer = await self._uow.viewers.get_by_id(viewer_id)
            viewer.delete(now)
            await self._uow.commit()
            return viewer
