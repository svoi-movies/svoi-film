from commons.config import AppBaseSettings
from pydantic import PostgresDsn


class Config(AppBaseSettings):
    db_dsn: PostgresDsn
