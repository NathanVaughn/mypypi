import os

import flask
from loguru import logger

from app.files.base import BaseFiles


class LocalFiles(BaseFiles):
    def __init__(self, directory: str) -> None:
        self.directory = os.path.abspath(directory)
        # create the the directory to save files to
        os.makedirs(self.directory, exist_ok=True)

    def build_path(self, file_url: str) -> str:
        return os.path.join(self.directory, super().build_path(file_url))

    def check(self, file_url: str) -> bool:
        # checks if the file exists
        file_path = self.build_path(file_url)
        result = os.path.exists(file_path)

        logger.debug(f"Checking if file {file_path} exists: {result}")
        return result

    def save(self, file_url: str) -> str:
        # build path to save file to
        file_path = self.build_path(file_url)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        logger.debug(f"Saving {file_url} to {file_path}")

        # save the file
        with open(file_path, "wb") as f:
            for chunk in self.download(file_url):
                f.write(chunk)

        return file_path

    def retrieve(self, file_url: str) -> flask.Response:
        # make response to send the file
        file_path = self.build_path(file_url)
        logger.debug(f"Generating response URL for {file_path}")

        return flask.send_from_directory(
            os.path.dirname(file_path), os.path.basename(file_path)
        )

    def delete(self, file_url: str) -> None:
        file_path = self.build_path(file_url)
        logger.debug(f"Deleting file {file_path}")
        os.remove(file_path)
