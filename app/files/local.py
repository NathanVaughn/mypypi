import os

import flask

import app.libraries.hash
import app.libraries.url
from app.files.base import BaseFiles


class LocalFiles(BaseFiles):
    def __init__(self, directory: str) -> None:
        self.directory = os.path.abspath(directory)
        # create the the directory to save files to
        os.makedirs(self.directory, exist_ok=True)

    def build_path(self, file_url: str) -> str:
        # build path to the file using similar strategy to PyPi
        file_url_hash = app.libraries.hash.sha256_hash_string(file_url)

        folder1 = file_url_hash[:2]
        folder2 = file_url_hash[2:4]
        folder3 = file_url_hash[4:]
        filename = app.libraries.url.get_filename(file_url)

        return os.path.join(folder1, folder2, folder3, filename)

    def check(self, file_url: str) -> bool:
        # checks if the file exists
        return os.path.exists(os.path.join(self.directory, self.build_path(file_url)))

    def save(self, file_url: str) -> str:
        # build path to save file to
        file_path = os.path.join(self.directory, self.build_path(file_url))
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # save the file
        with open(file_path, "wb") as f:
            for chunk in self.download(file_url):
                f.write(chunk)

        return file_path

    def retrieve(self, file_url: str) -> flask.Response:
        # make response to send the file
        file_path = os.path.join(self.directory, self.build_path(file_url))
        return flask.send_from_directory(
            os.path.dirname(file_path), os.path.basename(file_path)
        )
