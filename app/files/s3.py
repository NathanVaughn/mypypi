import http
import urllib.parse
from typing import Optional

import cachetools.func
import flask
import s3fs
import werkzeug
from loguru import logger

from app.database import Database
from app.files.base import BaseFiles
from app.main import flask_app


class S3Files(BaseFiles):
    def __init__(
        self,
        database: Database,
        bucket: str,
        access_key: str,
        secret_key: str,
        endpoint_url: Optional[str] = None,
        region_name: Optional[str] = None,
        public: bool = False,
        prefix: Optional[str] = None,
    ) -> None:
        super().__init__(database)

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
        self.prefix = prefix

    def build_path(self, file_url: str) -> str:
        # normalize the url from filesystem paths
        path = super().build_path(file_url).replace("\\", "/")

        # add prefix
        if self.prefix:
            path = f"{self.prefix.rstrip('/')}/{path}"

        return f"{self.bucket}/{path}"

    def check(self, file_url: str) -> bool:
        file_path = self.build_path(file_url)
        return self.fs.exists(file_path)

    def save(self, file_url: str) -> str:
        file_path = self.build_path(file_url)
        logger.info(f"Uploading {file_url} to {file_path}")

        with self.fs.open(file_path, "wb") as f:
            for chunk in self.download(file_url):
                f.write(chunk)

        return self.fs.url(file_path, expires=flask_app.config["S3_KEY_TTL"])

    @cachetools.func.ttl_cache(
        maxsize=None, ttl=flask_app.config["FILE_URL_EXPIRATION"]
    )
    def retrieve(self, file_url: str) -> werkzeug.wrappers.Response:
        file_path = self.build_path(file_url)
        return_url: str = self.fs.url(file_path, expires=flask_app.config["S3_KEY_TTL"])

        if self._is_public:
            # remove the query parameters from the url, so pip
            # can cache it better
            return_url_parsed = urllib.parse.urlparse(return_url)
            return_url = return_url_parsed._replace(query="").geturl()

        redirect_code = http.HTTPStatus.TEMPORARY_REDIRECT
        if self._is_public:
            redirect_code = http.HTTPStatus.PERMANENT_REDIRECT

        logger.info(f"Redirecting to {return_url} with code {redirect_code}")
        return flask.redirect(return_url, code=redirect_code)

    def delete(self, file_url: str) -> None:
        file_path = self.build_path(file_url)
        logger.info(f"Deleting file {file_path}")
        self.fs.rm_file(file_path)
