import flask
from .json import json_bp
from .file import file_bp

npm_bp = flask.Blueprint("npm", __name__, url_prefix="/npm")
npm_bp.register_blueprint(json_bp)
npm_bp.register_blueprint(file_bp)