from http import HTTPStatus
from typing import Union

import flask
import werkzeug
from loguru import logger

from app.main import file_backend, storage_backend

files_bp = flask.Blueprint("files", __name__, url_prefix="/file")


@files_bp.route("/<string:filename>")
def proxy(filename: str) -> Union[flask.Response, werkzeug.wrappers.Response]:
    # validate hash
    logger.debug(f"Validating URL key {filename}")
    url = storage_backend.get_file_url_from_key(filename)

    if url is None:
        logger.info(f"URL key {filename} not found in database")
        return flask.abort(HTTPStatus.BAD_REQUEST)

    # get the file
    return file_backend.get(url)
