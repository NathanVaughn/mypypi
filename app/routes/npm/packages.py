import http
import json

import flask
from loguru import logger

import app.libraries.proxy
from app.main import cache

packages_bp = flask.Blueprint("packages", __name__)


@packages_bp.route("/<path:packagename>")
@cache.cached()
def package(packagename: str) -> flask.Response:
    # make request to upstream
    logger.debug(f"Getting upstream package for {packagename}")
    status_code, content, headers = app.libraries.proxy.reverse_proxy(
        f"{flask.current_app.config['UPSTREAM_URL']}/{packagename}"
    )
    if status_code != http.HTTPStatus.OK:
        return flask.Response(content, status_code, headers)

    # process json
    logger.debug(f"Processing JSON for {packagename}")

    package_data = json.loads(content)

    # rewrite urls
    versions = package_data["versions"]
    for version_data in versions.values():
        version_data["dist"][
            "tarball"
        ] = app.libraries.proxy.generate_proxy_file_url_npm(
            version_data["dist"]["tarball"]
        )

    # craft response
    return flask.Response(json.dumps(package_data), status_code, headers)
