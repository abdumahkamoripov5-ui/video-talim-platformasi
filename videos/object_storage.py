"""Private S3-compatible storage. Credentials never leave the server."""
import mimetypes
from tempfile import SpooledTemporaryFile

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.files import File
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


def client():
    return boto3.client(
        's3', endpoint_url=settings.AWS_ENDPOINT_URL_S3,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
        config=Config(signature_version='s3v4', s3={'addressing_style': 'path'},
                      request_checksum_calculation='when_required', response_checksum_validation='when_required',
                      connect_timeout=5, read_timeout=30, retries={'max_attempts': 2}),
    )


def signed_download(key, filename=None):
    params = {'Bucket': settings.MEDIA_BUCKET, 'Key': key}
    if filename:
        from urllib.parse import quote
        params['ResponseContentDisposition'] = "attachment; filename*=UTF-8''" + quote(filename, safe='')
    return client().generate_presigned_url('get_object', Params=params, ExpiresIn=settings.SIGNED_URL_EXPIRY)


@deconstructible
class PrivateObjectStorage(Storage):
    def _open(self, name, mode='rb'):
        if mode != 'rb':
            raise ValueError('Read-only file handle')
        output = SpooledTemporaryFile(max_size=2 * 1024**2, dir='/tmp')
        client().download_fileobj(settings.MEDIA_BUCKET, name, output)
        output.seek(0)
        return File(output, name=name)

    def _save(self, name, content):
        client().upload_fileobj(content, settings.MEDIA_BUCKET, name, ExtraArgs={
            'ContentType': getattr(content, 'content_type', None) or mimetypes.guess_type(name)[0] or 'application/octet-stream',
        })
        return name

    def exists(self, name):
        try:
            client().head_object(Bucket=settings.MEDIA_BUCKET, Key=name)
            return True
        except ClientError as exc:
            if exc.response['Error']['Code'] in {'404', 'NoSuchKey', 'NotFound'}:
                return False
            raise

    def size(self, name):
        return client().head_object(Bucket=settings.MEDIA_BUCKET, Key=name)['ContentLength']

    def delete(self, name):
        client().delete_object(Bucket=settings.MEDIA_BUCKET, Key=name)

    def url(self, name):
        return signed_download(name)
