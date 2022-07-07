import os
import threading
from typing import Any

from dynaconf import FlaskDynaconf
from flask import Flask, request
from loguru import logger
from redis import Redis
from werkzeug.wrappers.response import Response

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


# upstream
default_value("MODE", "pypi")

if flask_app.config["MODE"] == "pypi":
    default_value("UPSTREAM_URL", "https://pypi.org")
elif flask_app.config["MODE"] == "npm":
    default_value("UPSTREAM_URL", "https://registry.npmjs.org")
else:
    raise ValueError(f"Unknown mode: {flask_app.config['MODE']}")

flask_app.config["UPSTREAM_URL"] = flask_app.config["UPSTREAM_URL"].rstrip("/")

default_value("UPSTREAM_STRICT", False)

# data
default_value("DATA_DIRECTORY", "data")
default_value("FILE_STORAGE_DRIVER", "local")
default_value("FILE_STORAGE_DIRECTORY", "files")
default_value("S3_PUBLIC", False)

# persistent storage
default_value("REDIS_URL", "redis://localhost:6379")
default_value("REDIS_PREFIX", "mypypi")
default_value("CACHE_TIME", 1800)


# =============================================================================
# Set up backends
# =============================================================================

# create Redis client
redis_client = Redis.from_url(flask_app.config["REDIS_URL"], decode_responses=True)

# create database
from app.database import Database

database_backend = Database(redis_client)

# create proxy service
from app.proxy import Proxy

proxy = Proxy(database_backend)

# setup file storage
if flask_app.config["FILE_STORAGE_DRIVER"].lower() == "local":
    import app.files.local

    files_backend = app.files.local.LocalFiles(
        database_backend,
        os.path.join(
            flask_app.config["DATA_DIRECTORY"],
            flask_app.config["FILE_STORAGE_DIRECTORY"],
        ),
    )

elif flask_app.config["FILE_STORAGE_DRIVER"].lower() == "s3":
    import app.files.s3

    files_backend = app.files.s3.S3Files(
        database_backend,
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

# create downloader
from app.downloader import Downloader

downloader = Downloader(database_backend, files_backend)
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
