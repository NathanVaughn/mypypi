import abc
import os
import threading
from http import HTTPStatus
from typing import Generator, Union

import flask
import packaging.utils
import requests
import werkzeug
from loguru import logger

import app.libraries.hash
import app.libraries.url
from app.main import flask_app, storage_backend


class BaseFiles(abc.ABC):
    def build_path(self, file_url: str) -> str:
        """
        Given a remote file url, return the path to save/load the file.
        """
        filename = app.libraries.url.get_filename(file_url)
        if filename.endswith(".whl"):
            name, version, _, _ = packaging.utils.parse_wheel_filename(filename)
        else:
            name, version = packaging.utils.parse_sdist_filename(filename)

        return os.path.join(name, str(version), filename)

    def download(self, file_url: str) -> Generator[bytes, None, None]:
        """
        Download a remote file and return a generator of bytes.
        """
        logger.info(f"Downloading file: {file_url}")
        response = requests.get(file_url, stream=True)
        yield from response.iter_content(chunk_size=1024)

    def in_progress(self, file_url: str) -> bool:
        """
        Check if there is already a task in-progress to download/upload this file url.
        """
        return storage_backend.check_url_task(file_url)

    def get(self, file_url: str) -> Union[flask.Response, werkzeug.wrappers.Response]:
        """
        Given a remote file url, return a flask response.
        Will download the file if it does not exist.
        """
        logger.info(f"Getting file: {file_url}")
        if self.check(file_url):
            storage_backend.update_file_url_last_downloaded_time(file_url)
            return self.retrieve(file_url)

        # if a task not in progress
        if not self.in_progress(file_url):
            # download the file in a background thread
            process = threading.Thread(target=self.save_wrapper, args=(file_url,))
            process.start()

        # if strict about not sending to upstream
        if flask_app.config["UPSTREAM_STRICT"]:
            return flask.abort(HTTPStatus.SERVICE_UNAVAILABLE)

        # redirect to original url
        storage_backend.update_file_url_last_downloaded_time(file_url)
        logger.debug(f"Redirecting to {file_url}")
        return flask.redirect(file_url)

    def save_wrapper(self, file_url: str) -> None:
        """
        Wrapper around `save`.
        """
        storage_backend.add_url_task(file_url)
        try:
            self.save(file_url)
        finally:
            storage_backend.del_url_task(file_url)

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
