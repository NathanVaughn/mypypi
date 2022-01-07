import urllib.parse
from typing import Optional

import flask
import s3fs
from loguru import logger

from app.files.base import BaseFiles


class S3Files(BaseFiles):
    def __init__(
        self,
        bucket: str,
        access_key: str,
        secret_key: str,
        endpoint_url: Optional[str] = None,
        region_name: Optional[str] = None,
        public: bool = False,
    ) -> None:
        self.bucket = bucket

        client_kwargs = {}
        if endpoint_url is not None:
            client_kwargs["endpoint_url"] = endpoint_url
        if region_name is not None:
            client_kwargs["region_name"] = region_name

        self.fs = s3fs.S3FileSystem(
            key=access_key, secret=secret_key, client_kwargs=client_kwargs
        )

        self._is_public = public

    def build_path(self, file_url: str) -> str:
        path = super().build_path(file_url).replace("\\", "/")
        return f"{self.bucket}/{path}"

    def check(self, file_url: str) -> bool:
        file_path = self.build_path(file_url)
        result = self.fs.exists(file_path)

        logger.info(f"Checking if file {file_path} exists: {result}")
        return result

    def save(self, file_url: str) -> str:
        file_path = self.build_path(file_url)
        logger.info(f"Uploading {file_url} to {file_path}")

        with self.fs.open(file_path, "wb") as f:
            for chunk in self.download(file_url):
                f.write(chunk)  # type: ignore

        return self.fs.url(file_path, expires=10 * 60)  # type: ignore

    def retrieve(self, file_url: str) -> flask.Response:
        file_path = self.build_path(file_url)
        return_url = self.fs.url(file_path, expires=10 * 60)

        if self._is_public:
            # remove the query parameters from the url, so pip
            # can cache it better
            return_url_parsed = urllib.parse.urlparse(return_url)
            return_url_parsed._replace(query="")
            return_url = return_url_parsed.geturl()

        logger.info(f"Retrieving redirect url for {file_url} to {return_url}")
        return flask.redirect(return_url)  # type: ignore

    def delete(self, file_url: str) -> None:
        file_path = self.build_path(file_url)
        logger.info(f"Deleting file {file_path}")
        self.fs.remove(file_path)
