from typing import Union

import flask
import werkzeug

from app.main import file_backend, flask_app

files_bp = flask.Blueprint("files", __name__)

# this is split weirdly like this so Flask can differentiate the routes
@files_bp.route("/<path:packagename>/-/<string:filename>")
def proxy(
    packagename: str, filename: str
) -> Union[flask.Response, werkzeug.wrappers.Response]:
    # get the file
    return file_backend.get(
        f"{flask_app.config['UPSTREAM_URL']}/{packagename}/-/{filename}"
    )
