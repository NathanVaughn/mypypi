import abc
import multiprocessing
import os
from typing import Generator, Union

import flask
import requests
import werkzeug
from loguru import logger

import app.libraries.hash
import app.libraries.url
from app.main import storage_backend


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
        if not self.check(file_url):
            # if a task not in progress
            if not self.in_progress(file_url):
                # download the file in a background thread
                process = multiprocessing.Process(
                    target=self.save_wrapper, args=(file_url,)
                )
                process.start()

            # redirect to original url
            storage_backend.update_file_url_last_downloaded_time(file_url)
            logger.debug(f"Redirecting to {file_url}")
            return flask.redirect(file_url)

        storage_backend.update_file_url_last_downloaded_time(file_url)
        return self.retrieve(file_url)

    def save_wrapper(self, file_url: str) -> None:
        """
        Wrapper around `save`.
        """
        storage_backend.add_url_task(file_url)
        self.save(file_url)
        storage_backend.del_url_task(file_url)

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

    def delete(self, file_url: str) -> None:
        """
        Given a remote file url, delete the file from our storage.
        """
        raise NotImplementedError
