from http import HTTPStatus

import flask
from loguru import logger

from app.main import file_backend, storage_backend

files_bp = flask.Blueprint("files", __name__, url_prefix="/file")


@files_bp.route("/<string:filename>")
def proxy(filename: str) -> flask.Response:
    # get the file url from query parameters
    file_url = flask.request.args.get("url", default=None)
    token = flask.request.args.get("token", default=None)

    # if no file url is provided, return a bad request
    if file_url is None:
        logger.debug("No file url provided")
        return flask.abort(HTTPStatus.BAD_REQUEST) # type: ignore

    # if no token is provided, return unauthorized
    if token is None:
        logger.debug("No token provided")
        return flask.abort(HTTPStatus.UNAUTHORIZED) # type: ignore

    # validate token
    url_token = storage_backend.get_url_token(file_url)
    if url_token is None:
        logger.debug(f"URL {file_url} not found in database")
        return flask.abort(HTTPStatus.UNAUTHORIZED) # type: ignore

    elif url_token != token:
        logger.debug(f"Token {token} does not match token {url_token} in database")
        return flask.abort(HTTPStatus.UNAUTHORIZED) # type: ignore

    # get the file
    return file_backend.get(file_url)
