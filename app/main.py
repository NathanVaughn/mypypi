import os

import peewee as pw
from dynaconf import FlaskDynaconf
from flask import Flask, request
from flask.wrappers import Response
from flask_caching import Cache
from loguru import logger

flask_app = Flask(__name__)
FlaskDynaconf(flask_app, ENVVAR_PREFIX="MYPYPI")

# =============================================================================
# Set up default values
# =============================================================================

# dictionary syntax needs to be used so the updated settings copy correctly

# config upstream
if "UPSTREAM_URL" not in flask_app.config:
    flask_app.config["UPSTREAM_URL"] = "https://pypi.org"
flask_app.config["UPSTREAM_URL"] = flask_app.config.UPSTREAM_URL.rstrip("/")

if "UPSTREAM_STRICT" not in flask_app.config:
    flask_app.config["UPSTREAM_STRICT"] = False

# caching
if "CACHE_TYPE" not in flask_app.config:
    flask_app.config["CACHE_TYPE"] = "SimpleCache"

if "CACHE_DEFAULT_TIMEOUT" not in flask_app.config:
    flask_app.config["CACHE_DEFAULT_TIMEOUT"] = 30 * 60
flask_app.config["CACHE_KEY_PREFIX"] = "mypypi_"

# data
if "DATA_DIRECTORY" not in flask_app.config:
    flask_app.config["DATA_DIRECTORY"] = "data"

if "FILE_STORAGE_DRIVER" not in flask_app.config:
    flask_app.config["FILE_STORAGE_DRIVER"] = "local"

if "FILE_STORAGE_DIRECTORY" not in flask_app.config:
    flask_app.config["FILE_STORAGE_DIRECTORY"] = "files"

if "S3_PUBLIC" not in flask_app.config:
    flask_app.config["S3_PUBLIC"] = False

# persistent storage
if "DATABASE_DRIVER" not in flask_app.config:
    flask_app.config["DATABASE_DRIVER"] = "sqlite"

if "DATABASE_NAME" not in flask_app.config:
    flask_app.config["DATABASE_NAME"] = "mypypi"

if "DATABASE_USER" not in flask_app.config:
    flask_app.config["DATABASE_USER"] = "mypypi"

if (
    flask_app.config.DATABASE_DRIVER == "mysql"
    and "DATABASE_PORT" not in flask_app.config
):
    flask_app.config["DATABASE_PORT"] = 3306

elif (
    flask_app.config.DATABASE_DRIVER == "postgres"
    and "DATABASE_PORT" not in flask_app.config
):
    flask_app.config["DATABASE_PORT"] = 5432

if "DATABASE_FILENAME" not in flask_app.config:
    flask_app.config["DATABASE_FILENAME"] = "database.sqlite"


# =============================================================================
# Set up extensions
# =============================================================================

cache = Cache(flask_app)

# =============================================================================
# Set up backends
# =============================================================================

# order matters, files depends on persistent storage
import app.storage.sql

if flask_app.config.DATABASE_DRIVER.lower() == "sqlite":
    if flask_app.config.DATABASE_FILENAME.lower() == ":memory:":
        _database = pw.SqliteDatabase(flask_app.config.DATABASE_FILENAME)
    else:
        _sqlite_path = os.path.join(
            flask_app.config.DATA_DIRECTORY, flask_app.config.DATABASE_FILENAME
        )
        os.makedirs(os.path.dirname(_sqlite_path), exist_ok=True)
        _database = pw.SqliteDatabase(_sqlite_path)
elif flask_app.config.DATABASE_DRIVER.lower() == "postgres":
    _database = pw.PostgresqlDatabase(
        flask_app.config.DATABASE_NAME,
        user=flask_app.config.DATABASE_USER,
        password=flask_app.config.DATABASE_PASSWORD,
        host=flask_app.config.DATABASE_HOST,
        port=flask_app.config.DATABASE_PORT,
    )
elif flask_app.config.DATABASE_DRIVER.lower() == "mysql":
    _database = pw.MySQLDatabase(
        flask_app.config.DATABASE_NAME,
        user=flask_app.config.DATABASE_USER,
        password=flask_app.config.DATABASE_PASSWORD,
        host=flask_app.config.DATABASE_HOST,
        port=flask_app.config.DATABASE_PORT,
    )
else:
    raise ValueError(f"Unknown database driver: {flask_app.config.DATABASE_DRIVER}")

storage_backend = app.storage.sql.SQLStorage(_database)

# setup file storage
if flask_app.config.FILE_STORAGE_DRIVER.lower() == "local":
    import app.files.local

    file_backend = app.files.local.LocalFiles(
        os.path.join(
            flask_app.config.DATA_DIRECTORY,
            flask_app.config.FILE_STORAGE_DIRECTORY,
        )
    )
elif flask_app.config.FILE_STORAGE_DRIVER.lower() == "s3":
    import app.files.s3

    file_backend = app.files.s3.S3Files(
        flask_app.config.S3_BUCKET,
        flask_app.config.S3_ACCESS_KEY,
        flask_app.config.S3_SECRET_KEY,
        endpoint_url=flask_app.config.get("S3_ENDPOINT_URL", None),
        region_name=flask_app.config.get("S3_REGION", None),
        public=flask_app.config.S3_PUBLIC,
        prefix=flask_app.config.get("S3_PREFIX", None),
    )
else:
    raise ValueError(
        f"Unknown file storage driver: {flask_app.config.FILE_STORAGE_DRIVER}"
    )

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

# =============================================================================
# Hooks
# =============================================================================


@flask_app.after_request
def _log_request(response: Response):
    """
    After each request, log the path and response code.
    """
    logger.info(f"{request.method} {request.full_path} {response.status_code}")
    return response


@flask_app.before_request
def _db_connect():
    """
    Before each request, connect to the database.
    """
    _database.connect(reuse_if_open=True)


@flask_app.teardown_request
def _db_close(exc):
    """
    After each request (no matter what), close the connection to the database.
    """
    if not _database.is_closed():
        _database.close()
