import http
import json

import flask
from loguru import logger

import app.libraries.proxy
from app.main import cache

url_prefix = "pypi"
url_postfix = "json"

json_bp = flask.Blueprint("json", __name__, url_prefix=f"/{url_prefix}")


def process_json(json_data: bytes) -> str:
    """
    Rewrite all file URLs in a json page with our file proxy.
    """
    data = json.loads(json_data)

    # ===================================
    # go through the urls in the releases
    releases = data["releases"]

    # make a list of all url objects that need updating
    url_objects = []
    for release in releases:
        for url_obj in releases[release]:
            url_objects.append(url_obj)

    # generate all the proxy urls
    proxy_urls = app.libraries.proxy.proxy_urls([u["url"] for u in url_objects])

    # rewrite the url objects
    for url_obj, proxy_url in zip(url_objects, proxy_urls):
        url_obj["url"] = proxy_url

    # ===================================
    # go through the urls in the urls
    urls = data["urls"]

    # make a list of all url objects that need updating
    # in this case, `urls` is a list of url objects
    url_objects = urls

    # generate all the proxy urls
    proxy_urls = app.libraries.proxy.proxy_urls([u["url"] for u in url_objects])

    # rewrite the url objects
    for url_obj, proxy_url in zip(url_objects, proxy_urls):
        url_obj["url"] = proxy_url

    return json.dumps(data, indent=4)


@json_bp.route(f"/<string:projectname>/{url_postfix}")
@cache.cached()
def project(projectname: str) -> flask.Response:
    # make request to upstream
    logger.debug(f"Getting upstream JSON for {projectname}")
    status_code, content, headers = app.libraries.proxy.reverse_proxy(
        f"{flask.current_app.config.UPSTREAM_PYPI_URL}/{url_prefix}/{projectname}/{url_postfix}"
    )
    if status_code != http.HTTPStatus.OK:
        return flask.Response(content, status_code, headers)

    # process json
    logger.debug(f"Processing JSON for {projectname}")
    new_json = process_json(content)

    # craft response
    return flask.Response(new_json, status_code, headers)


@json_bp.route(f"/<string:projectname>/<string:version>/{url_postfix}")
@cache.cached()
def project_version(projectname: str, version: str) -> flask.Response:
    # make request to upstream
    logger.debug(f"Getting upstream JSON for {projectname}/{version}")
    status_code, content, headers = app.libraries.proxy.reverse_proxy(
        f"{flask.current_app.config.UPSTREAM_PYPI_URL}/{url_prefix}/{projectname}/{version}/{url_postfix}"
    )

    if status_code != http.HTTPStatus.OK:
        return flask.Response(content, status_code, headers)

    # process json
    logger.debug(f"Processing JSON for {projectname}/{version}")
    new_json = process_json(content)

    # craft response
    return flask.Response(new_json, status_code, headers)
