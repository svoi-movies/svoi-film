from commons.config import AppBaseSettings
from pydantic import AmqpDsn, BaseModel


class SmtpConfig(BaseModel):
    host: str
    port: int
    user: str
    password: str


class Config(AppBaseSettings):
    rabbit_dsn: AmqpDsn
    smtp: SmtpConfig
