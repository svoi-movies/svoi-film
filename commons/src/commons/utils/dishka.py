from dishka import Provider, provide

from commons.utils.common_providers import (
    DateTimeProvider,
    DefaultDateTimeProvider,
    DefaultUUIDProvider,
    UUIDProvider,
)


class CommonProvidersProvider(Provider):

    uuid_provider = provide(DefaultUUIDProvider, provides=UUIDProvider)
    date_time_provider = provide(DefaultDateTimeProvider, provides=DateTimeProvider)
