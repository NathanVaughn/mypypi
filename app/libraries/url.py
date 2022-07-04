import os
from urllib.parse import urlparse

from app.main import flask_app


def get_filename(url: str) -> str:
    """
    Given a file url, return the filename.
    """
    return os.path.basename(urlparse(url).path)


def generate_url_key(url: str) -> str:
    """
    Generate a url key from a url.
    """
    if flask_app.config["MODE"] == "pypi":
        # in Python land, the filename is globally unique
        return get_filename(url)
    else:
        # in NPM land, the filename is not unique, as multiple namespaces
        # can have the same file
        return urlparse(url).path
