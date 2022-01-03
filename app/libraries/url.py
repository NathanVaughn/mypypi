import os
from urllib.parse import urlparse


def get_filename(url: str) -> str:
    """
    Given a file url, return the filename.
    """
    return os.path.basename(urlparse(url).path)
