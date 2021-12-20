from typing import Dict, Optional

import os
import tarfile
import tempfile
from minio import Minio


class Source:
  def source_type(self) -> str:
    return 'unknown'

  def fields(self) -> Dict[str, Optional[str]]:
    return {}

  def as_dict(self) -> Dict[str, Dict[str, Optional[str]]]:
    return {self.source_type(): self.fields()}


class GitSource(Source):
  def __init__(self, url: str, username: Optional[str],
               password: Optional[str]) -> None:
    self.url = url
    self.username = username
    self.password = password

  def source_type(self) -> str:
    return 'git'

  def fields(self) -> Dict[str, Optional[str]]:
    return {
        'url': self.url,
        'username': self.username,
        'password': self.password
    }


class MinioSource(Source):
  def __init__(self,
               endpoint: str,
               bucket: str,
               path: str,
               access_key: Optional[str] = None,
               secret_key: Optional[str] = None,
               upload_local_path: Optional[str] = None) -> None:
    self.endpoint = endpoint
    self.bucket = bucket
    self.path = path
    self.access_key = access_key
    self.secret_key = secret_key

    if upload_local_path:
      # this will overwrite existing object
      dirpath = tempfile.mkdtemp()
      tarball = os.path.join(dirpath, 'source.tar.gz')
      with tarfile.open(tarball, mode='w:gz') as archive:
        archive.add(upload_local_path)
      # secure=False here to avoid `ssl wrong version number` error
      client = Minio(endpoint=endpoint,
                     access_key=access_key,
                     secret_key=secret_key,
                     secure=False)
      client.fput_object(bucket_name=bucket,
                         object_name=path,
                         file_path=tarball)

  def source_type(self) -> str:
    return 'minio'

  def fields(self) -> Dict[str, Optional[str]]:
    return {
        'endpoint': self.endpoint,
        'bucket': self.bucket,
        'path': self.path,
        'accessKey': self.access_key,
        'secretKey': self.secret_key,
    }
