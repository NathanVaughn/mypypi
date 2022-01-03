from http import HTTPStatus

import flask
from loguru import logger

from app.main import file_backend, storage_backend

files_bp = flask.Blueprint("files", __name__, url_prefix="/file")


@files_bp.route("/<string:hash_>/<string:filename>")
def proxy(hash_: str, filename: str) -> flask.Response:
    # validate hash
    url = storage_backend.get_url_from_hash(hash_)

    if url is None:
        logger.debug(f"URL hash {hash_} not found in database")
        return flask.abort(HTTPStatus.BAD_REQUEST)  # type: ignore

    # get the file
    return file_backend.get(url)
