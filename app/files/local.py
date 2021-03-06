import os

import flask
from loguru import logger

from app.database import Database
from app.files.base import BaseFiles


class LocalFiles(BaseFiles):
    def __init__(self, database: Database, directory: str) -> None:
        super().__init__(database)

        self.directory = os.path.abspath(directory)
        # create the the directory to save files to
        os.makedirs(self.directory, exist_ok=True)

    def build_path(self, file_url: str) -> str:
        return os.path.join(self.directory, super().build_path(file_url))

    def check(self, file_url: str) -> bool:
        # checks if the file exists
        file_path = self.build_path(file_url)
        lock_file = f"{file_path}.lock"

        result = os.path.exists(file_path)

        # check if lock file exists, means we're still downloading
        if os.path.exists(lock_file):
            result = False

        return result

    def save(self, file_url: str) -> str:
        # build path to save file to
        file_path = self.build_path(file_url)
        lock_file = f"{file_path}.lock"

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        logger.info(f"Saving {file_url} to {file_path}")

        # create a lock file to denote download is in progress
        with open(lock_file, "w") as f:
            f.write("")

        # save the file
        with open(file_path, "wb") as f:
            for chunk in self.download(file_url):
                f.write(chunk)

        # remove lock file
        os.remove(lock_file)

        return file_path

    def retrieve(self, file_url: str) -> flask.Response:
        # make response to send the file
        file_path = self.build_path(file_url)
        return flask.send_from_directory(
            os.path.dirname(file_path), os.path.basename(file_path), as_attachment=True
        )

    def delete(self, file_url: str) -> None:
        file_path = self.build_path(file_url)
        logger.info(f"Deleting file {file_path}")
        os.remove(file_path)
