import os

from commons.unit_of_work.dishka import DbConfig
from pydantic import AmqpDsn, BaseModel
from pydantic_settings import (
    BaseSettings,
    DotEnvSettingsSource,
    EnvSettingsSource,
    NestedSecretsSettingsSource,
    SettingsConfigDict,
)


class RabbitConfig(BaseModel):
    dsn: AmqpDsn


class Config(BaseSettings):
    db: DbConfig
    rabbit: RabbitConfig

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        return (
            init_settings,
            DotEnvSettingsSource(
                settings_cls,
                env_file=os.environ.get("APP_DOTENV_FILE_PATH", ".env"),
                env_prefix="APP_",
            ),
            NestedSecretsSettingsSource(
                file_secret_settings,
                secrets_dir=os.environ.get("APP_SECRET_DIR_PATH", "./secrets"),
                secrets_dir_missing="error",
                case_sensitive=False,
                secrets_nested_subdir=True,
            ),
            EnvSettingsSource(settings_cls, env_prefix="APP_"),
        )
