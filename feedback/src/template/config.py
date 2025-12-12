from functools import cache
from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class JwtConfig(BaseModel):
    model_config = SettingsConfigDict(env_prefix="JWT_")
    verification_key_path: Path

    @cache
    def read_verification_key(self) -> str:
        with open(self.verification_key_path) as key_file:
            return key_file.read()


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_")

    jwt: JwtConfig


config = Config()
