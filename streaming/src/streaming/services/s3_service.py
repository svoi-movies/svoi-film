from uuid import UUID

import boto3
from botocore.client import Config as BotoConfig

from streaming.config import S3Config


class S3Service:
    def __init__(self, config: S3Config) -> None:
        self._config = config
        self._client = boto3.client(
            "s3",
            endpoint_url=config.endpoint_url,
            aws_access_key_id=config.access_key_id,
            aws_secret_access_key=config.secret_access_key,
            region_name=config.region_name,
            config=BotoConfig(signature_version="s3v4"),
        )

    def generate_upload_presigned_url(self, episode_id: UUID) -> tuple[str, str]:
        s3_key = f"episodes/{episode_id}/source.mp4"
        url = self._client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self._config.bucket_name,
                "Key": s3_key,
                "ContentType": "video/mp4",
            },
            ExpiresIn=self._config.upload_expiration_seconds,
        )
        return url, s3_key

    def generate_download_presigned_url(self, s3_key: str) -> str:
        url = self._client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self._config.bucket_name,
                "Key": s3_key,
            },
            ExpiresIn=self._config.download_expiration_seconds,
        )
        return url

    def check_object_exists(self, s3_key: str) -> bool:
        try:
            self._client.head_object(Bucket=self._config.bucket_name, Key=s3_key)
            return True
        except Exception:
            return False
