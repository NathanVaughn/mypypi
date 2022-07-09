import abc
import os
from http import HTTPStatus
from typing import Generator

import flask
import requests
import requests.auth
import werkzeug
from loguru import logger

import app.libraries.url
from app.database import Database
from app.main import flask_app


class BaseFiles(abc.ABC):
    def __init__(self, database: Database) -> None:
        self.database = database

    def build_path(self, file_url: str) -> str:
        """
        Given a remote file url, return the path to save/load the file.
        """
        if flask_app.config["PACKAGE_TYPE"] == "npm":
            package, filename = app.libraries.url.parse_npm_file_url(file_url)
            return os.path.join(*package.split("/"), filename)
        else:
            package, version = app.libraries.url.parse_pypi_file_url(file_url)
            return os.path.join(
                package, version, app.libraries.url.url_filename(file_url)
            )

    def download(self, file_url: str) -> Generator[bytes, None, None]:
        """
        Download a remote file and return a generator of bytes.
        """
        kwargs = {}

        # add credentials if they are configured
        if (
            "UPSTREAM_USERNAME" in flask_app.config
            and "UPSTREAM_PASSWORD" in flask_app.config
        ):
            kwargs["auth"] = requests.auth.HTTPBasicAuth(
                flask_app.config["UPSTREAM_USERNAME"],
                flask_app.config["UPSTREAM_PASSWORD"],
            )

        response = requests.get(
            file_url, stream=True, headers={"User-Agent": "mypypi 1.0"}, **kwargs
        )

        # don't save 404 data for example
        response.raise_for_status()

        yield from response.iter_content(chunk_size=1024)

    def get(self, file_url: str) -> werkzeug.wrappers.Response:
        """
        Given a remote file url, return a flask response.
        Will download the file if it does not exist.
        """
        # if we already have the file
        if self.check(file_url):
            return self.retrieve(file_url)

        # if a task not in progress
        if not self.database.check_file_download_job(file_url):
            self.database.add_file_download_job(file_url)

        # if strict about not sending to upstream
        if flask_app.config["UPSTREAM_STRICT"]:
            return flask.abort(HTTPStatus.SERVICE_UNAVAILABLE)

        # redirect to original url
        logger.debug(f"Redirecting to {file_url}")
        # temporary redirect
        return flask.redirect(file_url, code=HTTPStatus.FOUND)

    @abc.abstractmethod
    def check(self, file_url: str) -> bool:
        """
        Given a remote file url, return whether or not we have the file already.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def save(self, file_url: str) -> str:
        """
        Given a remote file url, download and save the file to our storage.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def retrieve(self, file_url: str) -> flask.Response:
        """
        Given a remote file url, return a flask response.
        We must have the file already.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def delete(self, file_url: str) -> None:
        """
        Given a remote file url, delete the file from our storage.
        """
        raise NotImplementedError
