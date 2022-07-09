import http
from urllib.parse import unquote

import cachetools.func
import flask
import orjson

import app.libraries.url
from app.main import database_backend, flask_app, proxy

url_prefix = "pypi"
url_postfix = "json"
json_bp = flask.Blueprint("json", __name__, url_prefix=f"/{url_prefix}")


@cachetools.func.ttl_cache(maxsize=None, ttl=flask_app.config["FILE_URL_EXPIRATION"])
def process_json(json_data: str) -> str:
    """
    Rewrite all file URLs in a json page with our file proxy.
    """
    data = orjson.loads(json_data)

    # ===================================
    # go through the urls in the releases
    release_datas = []
    for rd in data["releases"].values():
        release_datas.extend(rd)

    # make list of all filekey, url pairs
    filekey_url_pairs = [
        (app.libraries.url.url_filename(release_data["url"], True), release_data["url"])
        for release_data in release_datas
    ]

    # bulk insert
    database_backend.bulk_add_file_url_keys(filekey_url_pairs)

    # rewrite the release urls
    for filekey_url_pair, release_data in zip(filekey_url_pairs, release_datas):
        release_data["url"] = unquote(
            flask.url_for(
                "files.proxy",
                filekey=filekey_url_pair[0],
                _external=True,
            )
        )

    # ===================================
    # go through the urls in the urls
    # the file keys should have already been captured, no need to redo
    for url in data["urls"]:
        url["url"] = unquote(
            flask.url_for(
                "files.proxy",
                filekey=app.libraries.url.url_filename(url["url"], True),
                _external=True,
            )
        )

    return orjson.dumps(data, option=orjson.OPT_INDENT_2).decode("utf-8")


@json_bp.route(f"/<string:projectname>/{url_postfix}")
def project(projectname: str) -> flask.Response:
    # get the cached data from the upstream
    url_cache = proxy.get(
        f"{flask_app.config['UPSTREAM_URL']}/{url_prefix}/{projectname}/{url_postfix}"
    )

    # if the response is bad, return as-is
    if url_cache["status_code"] != http.HTTPStatus.OK:
        return flask.Response(
            url_cache["content"],
            url_cache["status_code"],
            url_cache["headers"],
        )

    # craft response
    return flask.Response(
        process_json(url_cache["content"]),
        url_cache["status_code"],
        url_cache["headers"],
    )


@json_bp.route(f"/<string:projectname>/<string:version>/{url_postfix}")
def project_version(projectname: str, version: str) -> flask.Response:
    # get the cached data from the upstream
    url_cache = proxy.get(
        f"{flask_app.config['UPSTREAM_URL']}/{url_prefix}/{projectname}/{version}/{url_postfix}"
    )

    # if the response is bad, return as-is
    if url_cache["status_code"] != http.HTTPStatus.OK:
        return flask.Response(
            url_cache["content"],
            url_cache["status_code"],
            url_cache["headers"],
        )

    # craft response
    return flask.Response(
        process_json(url_cache["content"]),
        url_cache["status_code"],
        url_cache["headers"],
    )
