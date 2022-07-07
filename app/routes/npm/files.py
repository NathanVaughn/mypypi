import flask
import werkzeug

from app.main import files_backend, flask_app

files_bp = flask.Blueprint("files", __name__)

# this is split weirdly like this so Flask can differentiate the routes
@files_bp.route("/<path:package>/-/<string:filename>")
def proxy(package: str, filename: str) -> werkzeug.wrappers.Response:
    return files_backend.get(
        f"{flask_app.config['UPSTREAM_URL']}/{package}/-/{filename}"
    )
