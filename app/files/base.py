import abc
from typing import Generator

import flask
import requests
from loguru import logger


class BaseFiles(abc.ABC):
    def download(self, file_url: str) -> Generator[bytes, None, None]:
        """
        Download a file and return a generator of bytes.
        """
        logger.debug(f"Downloading file: {file_url}")
        response = requests.get(file_url, stream=True)
        yield from response.iter_content(chunk_size=1024)

    def get(self, file_url: str) -> flask.Response:
        """
        Given a file url, return a flask response. Will download the file if it does not
        exist.
        """
        logger.debug(f"Getting file: {file_url}")
        if not self.check(file_url):
            self.save(file_url)

        return self.retrieve(file_url)

    def check(self, file_url: str) -> bool:
        """
        Given a file url, return whether or not the file exists.
        """
        raise NotImplementedError

    def save(self, file_url: str) -> str:
        """
        Given a file url, download and save the file.
        """
        raise NotImplementedError

    def retrieve(self, file_url: str) -> flask.Response:
        """
        Given a file url, return a flask response. File must already exist.
        """
        raise NotImplementedError
