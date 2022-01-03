import json
from http import HTTPStatus
from typing import List, Tuple
from urllib.parse import urlparse

import flask
import requests
from loguru import logger

from app.libraries.url import get_filename
from app.main import storage_backend


def use_cache(url: str) -> Tuple[int, bytes, List[Tuple[str, str]]]:
    logger.debug(f"Using cache for {url}")

    result = storage_backend.get_url_cache(url)
    assert result is not None

    return result[0], result[1], json.loads(result[2])


def reverse_proxy(url: str) -> Tuple[int, bytes, List[Tuple[str, str]]]:
    """
    Makes reverse proxy request and returns the response object, and applicable headers
    """
    # if a record exists and is still valid
    if storage_backend.is_url_cache_valid(url, flask.current_app.config.UPSTREAM_TTL):
        return use_cache(url)

    # make request to upstream
    logger.debug(f"Proxying request to {url}")

    # if request fails, use cache
    try:
        resp = requests.get(url)
    except requests.exceptions.RequestException as e:
        logger.error(e)
        return use_cache(url)

    # if the request had an internal server error, or other type of similar error,
    # use cache
    if resp.status_code >= HTTPStatus.INTERNAL_SERVER_ERROR:
        logger.error(f"Response had bad status code {resp.status_code}")
        return use_cache(url)

    # exclude certain headers
    excluded_headers = [
        "content-encoding",  # should be the same, but just in case
        "transfer-encoding",
        "connection",
        "content-length",  # this will change as our url lengths change
        "server",  # server software is different
        "x-served-by",
        "date",  # time will be different
    ]
    headers = [
        (name, value)
        for (name, value) in resp.raw.headers.items()
        if name.lower() not in excluded_headers
    ]

    # if we've made it this far, safe to delete old item from cache
    storage_backend.del_url_cache(url)

    # insert new item into cache
    logger.debug(f"Inserting {url} into cache")
    storage_backend.set_url_cache(
        url, resp.status_code, resp.content, json.dumps(headers)
    )

    return use_cache(url)


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
