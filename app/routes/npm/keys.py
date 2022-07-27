import flask
import werkzeug

from app.main import flask_app, proxy

keys_bp = flask.Blueprint("keys", __name__)


@keys_bp.route("/-/npm/v1/keys")
def keys() -> werkzeug.wrappers.Response:
    url_cache = proxy.get(f"{flask_app.config['UPSTREAM_URL']}/-/npm/v1/keys")

    # craft response
    return flask.Response(
        url_cache["content"], url_cache["status_code"], url_cache["headers"]
    )
