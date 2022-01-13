import flask
from .simple import simple_bp
from .json import json_bp

pypi_bp = flask.Blueprint("pypi", __name__, url_prefix="/pypi")
pypi_bp.register_blueprint(simple_bp)
pypi_bp.register_blueprint(json_bp)