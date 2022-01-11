import json
from http import HTTPStatus
from typing import List, Tuple
from urllib.parse import urlparse

import flask
import requests
import requests.auth
from loguru import logger

from app.libraries.url import get_filename
from app.main import flask_app, storage_backend


def use_url_cache(url: str) -> Tuple[int, bytes, List[Tuple[str, str]]]:
    """
    Loads the URL from cache and returns the
    status code, response content, and applicable headers
    """
    logger.info(f"Using cache for {url}")

    result = storage_backend.get_url_cache(url)
    assert result is not None

    return result[0], result[1], json.loads(result[2])


def reverse_proxy(url: str) -> Tuple[int, bytes, List[Tuple[str, str]]]:
    """
    Proxies request and returns the
    status code, response content, and applicable headers
    """
    logger.info(f"Proxying request to {url}")

    # if a record exists and is still valid
    if storage_backend.is_url_cache_valid(
        url, flask.current_app.config.CACHE_DEFAULT_TIMEOUT
    ):
        return use_url_cache(url)

    # if request fails, use cache
    try:
        # make request to upstream
        kwargs = {}
        if (
            "UPSTREAM_USERNAME" in flask_app.config
            and "UPSTREAM_PASSWORD" in flask_app.config
        ):
            kwargs["auth"] = requests.auth.HTTPBasicAuth(
                flask_app.config.UPSTREAM_USERNAME,
                flask_app.config.UPSTREAM_PASSWORD,
            )
        resp = requests.get(url, headers={"User-Agent": "mypypi 1.0"}, **kwargs)
    except requests.exceptions.RequestException as e:
        logger.error(e)
        return use_url_cache(url)

    # if the request had an internal server error, or other type of similar error,
    # use cache
    if resp.status_code >= HTTPStatus.INTERNAL_SERVER_ERROR:
        logger.error(f"Response had bad status code {resp.status_code}")
        return use_url_cache(url)

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

    # insert new item into cache
    logger.info(f"Inserting {url} into cache")
    storage_backend.set_url_cache(
        url, resp.status_code, resp.content, json.dumps(headers)
    )

    return use_url_cache(url)


def generate_proxy_file_url(url: str, hash_: str) -> str:
    """
    Given a file url and hash, return the proxy url.
    """
    # need to extract the url fragement, as it contains the hash
    parsed = urlparse(url)
    fragment = parsed.fragment

    # create proxy url with fragment on end
    # filename is not used on our end, but pip looks at it to
    # determine an applicable version
    new_url = flask.url_for(
        "files.proxy",
        hash_=hash_,
        filename=get_filename(url),
        _external=True,
    )

    # flask tries to url encode the anchor which we don't want
    # don't include fragment if there wasn't one before
    if fragment:
        new_url = f"{new_url}#{fragment}"

    return new_url


def proxy_urls(urls: List[str]) -> List[str]:
    """
    Given a list of file urls, return a list of proxy urls.
    """
    # create database entries in bulk for urls not in the database
    # more efficient than one at a time
    hashes = storage_backend.get_or_create_file_url_hashes(urls)

    # for url, hash_ in zip(urls, hashes):
    #     assert sha256_string(url) == hash_

    # now go through normal proxy_url function
    return [generate_proxy_file_url(url, hash_) for url, hash_ in zip(urls, hashes)]
