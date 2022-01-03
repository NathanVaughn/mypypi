import os

from dynaconf import FlaskDynaconf
from flask import Flask

import app.files.base
import app.storage.base

flask_app = Flask(__name__)
FlaskDynaconf(flask_app, ENVVAR_PREFIX="MYPYPI")

# =============================================================================
# Configure Flask before setting up routes
# =============================================================================

# config upstream
if "UPSTREAM_URL" not in flask_app.config:
    flask_app.config.UPSTREAM_URL = "https://pypi.org"
flask_app.config.UPSTREAM_URL = flask_app.config.UPSTREAM_URL.rstrip("/")

if "UPSTREAM_TTL" not in flask_app.config:
    flask_app.config.UPSTREAM_TTL = 30 * 60

# data
if "DATA_DIRECTORY" not in flask_app.config:
    flask_app.config.DATA_DIRECTORY = "data"

# files
if "LOCAL_FILES_DIRECTORY" not in flask_app.config:
    flask_app.config.LOCAL_FILES_DIRECTORY = "files"

# build path to store files
files_dir = os.path.join(
    flask_app.config.DATA_DIRECTORY,
    flask_app.config.LOCAL_FILES_DIRECTORY,
)

# persistent storage
if "SQLITE_FILENAME" not in flask_app.config:
    flask_app.config.SQLITE_FILENAME = "database.sqlite"

sqlite_filepath = os.path.join(
    flask_app.config.DATA_DIRECTORY, flask_app.config.SQLITE_FILENAME
)

# =============================================================================
# Set up backends
# =============================================================================

# order matters, files depends on persistent storage
import app.storage.sql

storage_backend = app.storage.sql.SQLStorage(sqlite_filepath)

import app.files.local

file_backend = app.files.local.LocalFiles(files_dir)

# =============================================================================
# Set up routes
# =============================================================================

from app.routes.files import files_bp
from app.routes.json import json_bp
from app.routes.simple import simple_bp

# pypi routes
flask_app.register_blueprint(simple_bp)
flask_app.register_blueprint(json_bp)

# our internal routes
flask_app.register_blueprint(files_bp)
