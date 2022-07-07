import http
import json
import urllib.parse

import flask

import app.libraries.url
from app.main import flask_app, proxy

packages_bp = flask.Blueprint("packages", __name__)


@packages_bp.route("/<path:package>")
def package(package: str) -> flask.Response:
    # get the cached data from the upstream
    url_cache = proxy.get(f"{flask_app.config['UPSTREAM_URL']}/{package}")

    # if the response is bad, return as-is
    if url_cache["status_code"] != http.HTTPStatus.OK:
        return flask.Response(
            url_cache["content"],
            url_cache["status_code"],
            url_cache["headers"],
        )

    # rewrite urls
    package_data = json.loads(url_cache["content"])
    for version_data in package_data["versions"].values():
        # parse the filename
        package, filename = app.libraries.url.parse_npm_file_url(
            version_data["dist"]["tarball"]
        )

        # rebuild the URL
        version_data["dist"]["tarball"] = urllib.parse.unquote(
            flask.url_for(
                "files.proxy",
                filename=filename,
                package=package,
                _external=True,
            )
        )

    # craft response
    return flask.Response(
        json.dumps(package_data), url_cache["status_code"], url_cache["headers"]
    )
