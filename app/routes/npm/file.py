import http
import json

import flask
import werkzeug
from loguru import logger

import app.libraries.hash
from app.main import cache
from app.main import file_backend, storage_backend

file_bp = flask.Blueprint("file", __name__)


@file_bp.route("/<string:packagename>/-/<string:filename>")
def package_file(packagename: str, filename: str) -> werkzeug.wrappers.Response:
    fileurl = f"{flask.current_app.config.UPSTREAM_NPM_URL}/{packagename}/-/{filename}"

    # get file from backend since this comes from a more trusted source
    return file_backend.get(fileurl)
