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
if "FILE_STORAGE" not in flask_app.config:
    flask_app.config.FILE_STORAGE = "local"

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

sqlite_file_path = os.path.join(
    flask_app.config.DATA_DIRECTORY, flask_app.config.SQLITE_FILENAME
)

# =============================================================================
# Set up backends
# =============================================================================

# order matters, files depends on persistent storage
import app.storage.sql

storage_backend = app.storage.sql.SQLStorage(sqlite_file_path)


# setup file storage
if flask_app.config.FILE_STORAGE == "local":
    import app.files.local

    file_backend = app.files.local.LocalFiles(files_dir)
elif flask_app.config.FILE_STORAGE == "s3":
    import app.files.s3

    file_backend = app.files.s3.S3Files(
        flask_app.config.S3_BUCKET,
        flask_app.config.S3_ACCESS_KEY,
        flask_app.config.S3_SECRET_KEY,
        endpoint_url=flask_app.config.get("S3_ENDPOINT_URL", None),
        region_name=flask_app.config.get("S3_REGION", None),
    )
else:
    raise ValueError("Invalid file storage backend")

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
