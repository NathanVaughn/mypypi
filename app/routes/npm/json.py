import http
import json

import flask
from loguru import logger

import app.libraries.proxy
from app.main import cache

json_bp = flask.Blueprint("json", __name__)


def process_all_json(json_data: bytes) -> str:
    """
    Rewrite all file URLs in a json page with our file proxy.
    """
    data = json.loads(json_data)

    # ===================================
    # go through the urls in the releases
    versions = data["versions"]

    # make a list of all url objects that need updating
    dist_objects = [versions[version]["dist"] for version in versions]

    # generate all the proxy urls
    proxy_urls = app.libraries.proxy.proxy_urls([f["tarball"] for f in dist_objects])

    # rewrite the url objects
    for dist_obj, proxy_url in zip(dist_objects, proxy_urls):
        dist_obj["tarball"] = proxy_url

    return json.dumps(data, indent=4)


def process_single_json(json_data: bytes) -> str:
    """
    Rewrite one file URL in a json page with our file proxy.
    """
    data = json.loads(json_data)
    data["dist"]["tarball"] = app.libraries.proxy.proxy_urls([data["dist"]["tarball"]])
    return json.dumps(data, indent=4)


@json_bp.route("/<string:packagename>")
@cache.cached()
def package(packagename: str) -> flask.Response:
    # make request to upstream
    logger.debug(f"Getting upstream JSON for {packagename}")
    status_code, content, headers = app.libraries.proxy.reverse_proxy(
        f"{flask.current_app.config.UPSTREAM_NPM_URL}/{packagename}"
    )
    if status_code != http.HTTPStatus.OK:
        return flask.Response(content, status_code, headers)

    # process json
    logger.debug(f"Processing JSON for {packagename}")
    new_json = process_all_json(content)

    # craft response
    return flask.Response(new_json, status_code, headers)


@json_bp.route("/<string:packagename>/<string:version>")
@cache.cached()
def package_version(packagename: str, version: str) -> flask.Response:
    # make request to upstream
    logger.debug(f"Getting upstream JSON for {packagename}/{version}")
    status_code, content, headers = app.libraries.proxy.reverse_proxy(
        f"{flask.current_app.config.UPSTREAM_NPM_URL}/{packagename}/{version}"
    )

    if status_code != http.HTTPStatus.OK:
        return flask.Response(content, status_code, headers)

    # process json
    logger.debug(f"Processing JSON for {packagename}/{version}")
    new_json = process_single_json(content)

    # craft response
    return flask.Response(new_json, status_code, headers)
