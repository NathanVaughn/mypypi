import os
from urllib.parse import urlparse

import flask

from app.main import storage_backend


def get_filename(url: str) -> str:
    """
    Given a file url, return the filename.
    """
    return os.path.basename(urlparse(url).path)


def proxy_url(url: str) -> str:
    """
    Given a file url, return the proxy url.
    """
    # get or create a token for the url
    token = storage_backend.get_url_token(url)
    if token is None:
        token = storage_backend.set_url_token(url)

    # need to extract the url fragement, as it contains the hash
    parsed = urlparse(url)
    fragment = parsed.fragment

    # create proxy url with fragment on end
    # filename is not used on our end, but pip looks at it to
    # determine an applicable version
    new_url = flask.url_for(
        "files.proxy",
        filename=get_filename(url),
        url=url,
        token=token,
        _external=True,
    )

    # flask tries to url encode the anchor which we don't want
    # don't include fragment if there wasn't one before
    if fragment:
        new_url = f"{new_url}#{fragment}"

    return new_url
