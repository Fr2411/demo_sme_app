from dataclasses import dataclass
from uuid import uuid4

import boto3

from backend.app.core.config import settings


@dataclass
class UploadedImage:
    bucket: str
    key: str
    url: str


class S3ImageStorageService:
    def __init__(self) -> None:
        self.bucket_name = settings.s3_bucket_name
        self.prefix = settings.s3_product_image_prefix.strip('/')
        self.client = boto3.client(
            's3',
            region_name=settings.s3_region,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
        )

    def upload_product_image(self, product_id: int, file_name: str, payload: bytes, content_type: str) -> UploadedImage:
        if not self.bucket_name:
            raise ValueError('S3 bucket configuration missing')

        extension = file_name.rsplit('.', 1)[-1] if '.' in file_name else 'bin'
        key = f'{self.prefix}/product-{product_id}/{uuid4().hex}.{extension}'

        self.client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=payload,
            ContentType=content_type,
        )
        url = f'https://{self.bucket_name}.s3.{settings.s3_region}.amazonaws.com/{key}'
        return UploadedImage(bucket=self.bucket_name, key=key, url=url)
