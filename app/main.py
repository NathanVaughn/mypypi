import os
import threading
from typing import Any

import peewee as pw
from dynaconf import FlaskDynaconf
from flask import Flask, request
from flask_caching import Cache
from loguru import logger
from werkzeug.wrappers.response import Response

from app.downloader import Downloader

flask_app = Flask(__name__)
FlaskDynaconf(flask_app, ENVVAR_PREFIX="MYPYPI")

# =============================================================================
# Set up default values
# =============================================================================


def default_value(key: str, value: Any) -> None:
    """
    Set the default value of the flask config.
    """
    flask_app.config[key] = flask_app.config.get(key, value)


default_value("MODE", "pypi")

# config upstream
if flask_app.config["MODE"] == "pypi":
    default_value("UPSTREAM_URL", "https://pypi.org")
elif flask_app.config["MODE"] == "npm":
    default_value("UPSTREAM_URL", "https://registry.npmjs.org")
else:
    raise ValueError(f"Unknown mode: {flask_app.config['MODE']}")

flask_app.config["UPSTREAM_URL"] = flask_app.config["UPSTREAM_URL"].rstrip("/")

default_value("UPSTREAM_STRICT", False)

# caching
default_value("CACHE_TYPE", "SimpleCache")
default_value("CACHE_DEFAULT_TIMEOUT", 30 * 60)
flask_app.config["CACHE_KEY_PREFIX"] = "mypypi_"

# data
default_value("DATA_DIRECTORY", "data")
default_value("FILE_STORAGE_DRIVER", "local")
default_value("FILE_STORAGE_DIRECTORY", "files")
default_value("S3_PUBLIC", False)

# persistent storage
default_value("DATABASE_DRIVER", "sqlite")
default_value("DATABASE_NAME", "mypypi")
default_value("DATABASE_USER", "mypypi")

if (
    flask_app.config["DATABASE_DRIVER"] == "mysql"
    and "DATABASE_PORT" not in flask_app.config
):
    flask_app.config["DATABASE_PORT"] = 3306

elif (
    flask_app.config["DATABASE_DRIVER"] == "postgres"
    and "DATABASE_PORT" not in flask_app.config
):
    flask_app.config["DATABASE_PORT"] = 5432

default_value("DATABASE_FILENAME", "database.sqlite")

# =============================================================================
# Set up extensions
# =============================================================================

cache = Cache(flask_app)

# =============================================================================
# Set up backends
# =============================================================================

# order matters, files depends on persistent storage
import app.storage.sql

if flask_app.config["DATABASE_DRIVER"].lower() == "sqlite":
    if flask_app.config["DATABASE_FILENAME"].lower() == ":memory:":
        _database = pw.SqliteDatabase(flask_app.config["DATABASE_FILENAME"])
    else:
        _sqlite_path = os.path.join(
            flask_app.config["DATA_DIRECTORY"], flask_app.config["DATABASE_FILENAME"]
        )
        os.makedirs(os.path.dirname(_sqlite_path), exist_ok=True)
        _database = pw.SqliteDatabase(_sqlite_path)

elif flask_app.config["DATABASE_DRIVER"].lower() == "postgres":
    _database = pw.PostgresqlDatabase(
        flask_app.config["DATABASE_NAME"],
        user=flask_app.config["DATABASE_USER"],
        password=flask_app.config["DATABASE_PASSWORD"],
        host=flask_app.config["DATABASE_HOST"],
        port=flask_app.config["DATABASE_PORT"],
    )

elif flask_app.config["DATABASE_DRIVER"].lower() == "mysql":
    _database = pw.MySQLDatabase(
        flask_app.config["DATABASE_NAME"],
        user=flask_app.config["DATABASE_USER"],
        password=flask_app.config["DATABASE_PASSWORD"],
        host=flask_app.config["DATABASE_HOST"],
        port=flask_app.config["DATABASE_PORT"],
    )
else:
    raise ValueError(f'Unknown database driver: {flask_app.config["DATABASE_DRIVER"]}')

storage_backend = app.storage.sql.SQLStorage(_database)

# setup file storage
if flask_app.config["FILE_STORAGE_DRIVER"].lower() == "local":
    import app.files.local

    file_backend = app.files.local.LocalFiles(
        os.path.join(
            flask_app.config["DATA_DIRECTORY"],
            flask_app.config["FILE_STORAGE_DIRECTORY"],
        )
    )

elif flask_app.config["FILE_STORAGE_DRIVER"].lower() == "s3":
    import app.files.s3

    file_backend = app.files.s3.S3Files(
        flask_app.config["S3_BUCKET"],
        flask_app.config["S3_ACCESS_KEY"],
        flask_app.config["S3_SECRET_KEY"],
        endpoint_url=flask_app.config.get("S3_ENDPOINT_URL", None),
        region_name=flask_app.config.get("S3_REGION", None),
        public=flask_app.config["S3_PUBLIC"],
        prefix=flask_app.config.get("S3_PREFIX", None),
    )

else:
    raise ValueError(
        f"Unknown file storage driver: {flask_app.config['FILE_STORAGE_DRIVER']}"
    )

downloader = Downloader(storage_backend, file_backend)
downloader_thread = threading.Thread(target=downloader.run)
downloader_thread.start()

# =============================================================================
# Set up routes
# =============================================================================

if flask_app.config["MODE"] == "pypi":
    from app.routes.pypi.files import files_bp
    from app.routes.pypi.json import json_bp
    from app.routes.pypi.simple import simple_bp

    # pypi routes
    flask_app.register_blueprint(simple_bp)
    flask_app.register_blueprint(json_bp)

    # our internal routes
    flask_app.register_blueprint(files_bp)

else:
    from app.routes.npm.files import files_bp
    from app.routes.npm.packages import packages_bp

    # npm routes
    flask_app.register_blueprint(files_bp)
    flask_app.register_blueprint(packages_bp)


# =============================================================================
# Hooks
# =============================================================================


@flask_app.after_request
def _log_request(response: Response) -> Response:
    """
    After each request, log the path and response code.
    """
    logger.info(f"{request.method} {request.full_path} {response.status_code}")
    return response


@flask_app.before_request
def _db_connect() -> None:
    """
    Before each request, connect to the database.
    """
    _database.connect(reuse_if_open=True)


@flask_app.teardown_request
def _db_close(exc: Any) -> None:
    """
    After each request (no matter what), close the connection to the database.
    """
    if not _database.is_closed():
        _database.close()
