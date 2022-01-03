import http
import json

import flask

import app.libraries.proxy
import app.libraries.url

url_prefix = "pypi"
url_postfix = "json"
json_bp = flask.Blueprint("json", __name__, url_prefix=f"/{url_prefix}")


def process_json(json_data: bytes) -> str:
    """
    Rewrite all file URLs in a json page with our file proxy.
    """
    data = json.loads(json_data)

    # go through the urls in the releases
    releases = data["releases"]
    for release in releases:
        for url in releases[release]:
            url["url"] = app.libraries.url.proxy_url(url["url"])

    # gor the urls in the urls
    urls = data["urls"]
    for url in urls:
        url["url"] = app.libraries.url.proxy_url(url["url"])

    return json.dumps(data, indent=4)


@json_bp.route("/<string:projectname>/json")
def project(projectname: str) -> flask.Response:
    # make request to upstream
    status_code, content, headers = app.libraries.proxy.reverse_proxy(
        f"{flask.current_app.config.UPSTREAM_URL}/{url_prefix}/{projectname}/{url_postfix}"
    )
    if status_code != http.HTTPStatus.OK:
        return flask.Response(content, status_code, headers)

    # process json
    new_json = process_json(content)

    # craft response
    return flask.Response(new_json, status_code, headers)


@json_bp.route("/<string:projectname>/<string:version>/json")
def project_version(projectname: str, version: str) -> flask.Response:
    # make request to upstream
    status_code, content, headers = app.libraries.proxy.reverse_proxy(
        f"{flask.current_app.config.UPSTREAM_URL}/{url_prefix}/{projectname}/{version}/{url_postfix}"
    )

    if status_code != http.HTTPStatus.OK:
        return flask.Response(content, status_code, headers)

    # process json
    new_json = process_json(content)

    # craft response
    return flask.Response(new_json, status_code, headers)
