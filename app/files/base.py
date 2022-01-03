import abc
import os
from typing import Generator

import flask
import requests
from loguru import logger

import app.libraries.hash
import app.libraries.url


class BaseFiles(abc.ABC):
    def build_path(self, file_url: str) -> str:
        """
        Given a remote file url, return the path to save/load the file.
        """
        file_url_hash = app.libraries.hash.sha256_string(file_url)

        folder1 = file_url_hash[:2]
        folder2 = file_url_hash[2:4]
        folder3 = file_url_hash[4:]
        filename = app.libraries.url.get_filename(file_url)

        return os.path.join(folder1, folder2, folder3, filename)

    def download(self, file_url: str) -> Generator[bytes, None, None]:
        """
        Download a remote file and return a generator of bytes.
        """
        logger.debug(f"Downloading file: {file_url}")
        response = requests.get(file_url, stream=True)
        yield from response.iter_content(chunk_size=1024)

    def get(self, file_url: str) -> flask.Response:
        """
        Given a remote file url, return a flask response.
        Will download the file if it does not exist.
        """
        logger.debug(f"Getting file: {file_url}")
        if not self.check(file_url):
            self.save(file_url)

        return self.retrieve(file_url)

    def check(self, file_url: str) -> bool:
        """
        Given a remote file url, return whether or not we have the file already.
        """
        raise NotImplementedError

    def save(self, file_url: str) -> str:
        """
        Given a remote file url, download and save the file to our storage.
        """
        raise NotImplementedError

    def retrieve(self, file_url: str) -> flask.Response:
        """
        Given a remote file url, return a flask response.
        We must have the file already.
        """
        raise NotImplementedError
