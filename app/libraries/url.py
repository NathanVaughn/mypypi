import os
from urllib.parse import urlparse


def get_filename(url: str) -> str:
    """
    Given a file url, return the filename.
    """
    return os.path.basename(urlparse(url).path)


def generate_url_key(url: str) -> str:
    """
    Generate a url key from a url
    """
    return get_filename(url)
