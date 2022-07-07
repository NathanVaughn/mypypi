import datetime
from http import HTTPStatus
from typing import Optional

import requests
import requests.auth
from loguru import logger

from app.database import Database
from app.main import flask_app
from app.models.url_cache import URLCache


class Proxy:
    def __init__(self, database: Database) -> None:
        self.database = database

    def _reverse_proxy(self, url: str) -> Optional[URLCache]:
        """
        Reverse proxy the request to the upstream server and return the response.
        Returns None if the request failed.
        """
        logger.debug(f"Proxying request to {url}")

        kwargs = {}

        # add credentials if they are configured
        if (
            "UPSTREAM_USERNAME" in flask_app.config
            and "UPSTREAM_PASSWORD" in flask_app.config
        ):
            kwargs["auth"] = requests.auth.HTTPBasicAuth(
                flask_app.config["UPSTREAM_USERNAME"],
                flask_app.config["UPSTREAM_PASSWORD"],
            )

        # make request to upstream
        try:
            resp = requests.get(url, headers={"User-Agent": "mypypi 1.0"}, **kwargs)
        except requests.exceptions.RequestException as e:
            # if request fails
            logger.error(e)
            return

        # if the request had an internal server error, or other type of similar error,
        # use cache
        if resp.status_code >= HTTPStatus.INTERNAL_SERVER_ERROR:
            logger.error(f"Response had bad status code {resp.status_code}")
            return None

        # otherwise, cache what we have

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

        url_cache = URLCache(
            status_code=resp.status_code,
            content=resp.content.decode("utf-8"),
            headers=headers,
        )

        # if we got to here, put the cache entry in the database
        self.database.set_url_cache(url, url_cache)

        return url_cache

    def get(self, url: str, max_age: int = flask_app.config["CACHE_TIME"]) -> URLCache:
        """
        Get an upstream URL from the cache or from the upstream server.
        """
        timestamp, url_cache = self.database.get_url_cache(url)

        # if there is no cache entry, try to reach the upstream server
        if timestamp is None or url_cache is None:
            url_cache2 = self._reverse_proxy(url)

            # couldn't reach upstream, return error
            if url_cache2 is None:
                return URLCache(
                    status_code=HTTPStatus.SERVICE_UNAVAILABLE, content="", headers=[]
                )

            # return response
            return url_cache2

        # if the cache entry is stale, try to reach the upstream server
        if (datetime.datetime.now() - timestamp).total_seconds() >= max_age:
            url_cache2 = self._reverse_proxy(url)

            # couldn't reach upstream, return what we have
            if url_cache2 is None:
                return url_cache

        # return original cache entry
        return url_cache
