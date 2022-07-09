from http import HTTPStatus

import flask
import werkzeug
from loguru import logger

import app.libraries.url
import app.routes.pypi.simple
from app.main import database_backend, files_backend

files_bp = flask.Blueprint("files", __name__, url_prefix="/file")


@files_bp.route("/<string:filekey>")
def proxy(filekey: str, recursed: bool = False) -> werkzeug.wrappers.Response:
    # lookup file key in database
    url = database_backend.get_file_url_from_key(filekey)

    if url is not None:
        # get the file
        return files_backend.get(url)

    if recursed:
        # if this is not the first time running this, return a 404
        return flask.abort(HTTPStatus.NOT_FOUND)

    # attempt to get the file url from the package page
    logger.warning(f"URL key {filekey} not found in database")

    try:
        project = app.libraries.url.parse_pypi_file_url(filekey)[0]
    except ValueError:
        # if the file key is improperly formatted, return a 404
        return flask.abort(HTTPStatus.NOT_FOUND)

    app.routes.pypi.simple.project(project)

    # re-run this route
    return proxy(filekey, recursed=True)
