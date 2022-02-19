# MyPyPi

This is a simple pull-through cache for any Python package index. It is meant as a way
to have a local cache of packages in case the source package index is down, speed
up CI/CD, etc. This is NOT a way to distribute custom packages interally.
For that, I recommend more advanced solutions like Artifactory, Azure Artifacts, etc.

Additionally, there is no concept of user accounts or authentication. If desired,
this is up to you to provide via a reverse proxy, network rules, etc.

## Setup

All environment variables begin with `MYPYPI_`.

| Name                            | Description                                                                                                                                                                                                                                                                                                                                            | Default                                      |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------- |
| `MYPYPI_UPSTREAM_URL`           | URL of the source package index. Do NOT include the trailing `/simple`.                                                                                                                                                                                                                                                                                | `https://pypi.org`                           |
| `MYPYPI_UPSTREAM_USERNAME`      | HTTP basic auth username for upstream.                                                                                                                                                                                                                                                                                                                 |                                              |
| `MYPYPI_UPSTREAM_PASSWORD`      | HTTP basic auth password for upstream.                                                                                                                                                                                                                                                                                                                 |                                              |
| `MYPYPI_UPSTREAM_STRICT`        | If `false`, will redirect requests to the upstream file source while a file is being cached the first time. If set to `true`, will return 503 until the file has been cached. `pip` usually handles this okay, but for large files, this may cause timeouts. This is good if you decided to completely block the upstream source at the network level. | `false`                                      |
| `MYPYPI_CACHE_DEFAULT_TIMEOUT`  | How long to cache upstream package versions, in seconds                                                                                                                                                                                                                                                                                                | `1800`                                       |
| `MYPYPI_DATA_DIRECTORY`         | Directory to store persistent data in. Can be absolute or relative to working directory                                                                                                                                                                                                                                                                | `data`                                       |
| `MYPYPI_FILE_STORAGE_DRIVER`    | What file storage driver to use. Valid values are `local` or `s3`                                                                                                                                                                                                                                                                                      | `local`                                      |
| `MYPYPI_FILE_STORAGE_DIRECTORY` | If using the local file storage, what directory relative to `DATA_DIRECTORY` to store package files in                                                                                                                                                                                                                                                 | `files`                                      |
| `MYPYPI_S3_BUCKET`              | If using S3 file storage, what bucket to store files in                                                                                                                                                                                                                                                                                                |                                              |
| `MYPYPI_S3_PREFIX`              | If using S3 file storage, an optional prefix to use                                                                                                                                                                                                                                                                                                    |                                              |
| `MYPYPI_S3_ACCESS_KEY`          | If using S3 file storage, the access key to use                                                                                                                                                                                                                                                                                                        |                                              |
| `MYPYPI_S3_SECRET_KEY`          | If using S3 file storage, the secret key to use. If the bucket is not public, this should have permission to create signed URLS                                                                                                                                                                                                                        |                                              |
| `MYPYPI_S3_ENDPOINT_URL`        | If using S3 file storage, alternative endpoint URL (not needed if using AWS). Protocol (`https://`) is required.                                                                                                                                                                                                                                       |                                              |
| `MYPYPI_S3_REGION`              | If using S3 file storage, region to use (may be required depending on provider)                                                                                                                                                                                                                                                                        |                                              |
| `MYPYPI_S3_PUBLIC`              | If using S3 file storage, whether or not the bucket is public. If it is, and this variable is set to `true`, then this will remove URL query parameters to help facilitate caching by `pip`.                                                                                                                                                           | `false`                                      |
| `MYPYPI_DATABASE_DRIVER`        | What database driver to use. Valid values are `sqlite`, `mysql`, or `postgres`                                                                                                                                                                                                                                                                         | `sqlite`                                     |
| `MYPYPI_DATABASE_NAME`          | If not using the SQLite driver, database name to use                                                                                                                                                                                                                                                                                                   | `mypypi`                                     |
| `MYPYPI_DATABASE_USER`          | If not using the SQLite driver, database account username                                                                                                                                                                                                                                                                                              | `mypypi`                                     |
| `MYPYPI_DATABASE_PASSWORD`      | If not using the SQLite driver, database account password                                                                                                                                                                                                                                                                                              |                                              |
| `MYPYPI_DATABASE_HOST`          | If not using the SQLite driver, database host to connect to                                                                                                                                                                                                                                                                                            |                                              |
| `MYPYPI_DATABASE_PORT`          | If not using the SQLite driver, database port to connect on                                                                                                                                                                                                                                                                                            | `3306` for `mysql` and `5432` for `postgres` |
| `MYPYPI_DATABASE_FILENAME`      | If using the SQLite driver, SQLite file relative to `DATA_DIRECTORY` to keep the database                                                                                                                                                                                                                                                              | `database.sqlite`                            |

Additionally, you can set any of the settings from
[Flask-Caching](https://flask-caching.readthedocs.io/en/latest/#configuring-flask-caching)
(you still need to add the `MYPYPI_` prefix to the setting name). By default,
`SimpleCache` is used for `CACHE_TYPE`.

## Example Configs

### Simple

```python
MYPYPI_UPSTREAM_URL="https://pypi.org"

MYPYPI_CACHE_DEFAULT_TIMEOUT=1800

MYPYPI_DATA_DIRECTORY="data"
MYPYPI_FILE_STORAGE_DRIVER="local"
MYPYPI_FILE_STORAGE_DIRECTORY="files"

MYPYPI_DATABASE_DRIVER="sqlite"
MYPYPI_DATABASE_FILENAME="database.sqlite"
```

### (More) Production Grade

```python
MYPYPI_UPSTREAM_URL="https://pypi.org"

MYPYPI_CACHE_TYPE="RedisCache"
MYPYPI_CACHE_REDIS_HOST="<host>"
MYPYPI_CACHE_REDIS_PORT=6379
MYPYPI_CACHE_DEFAULT_TIMEOUT=1800

MYPYPI_FILE_STORAGE_DRIVER="s3"
MYPYPI_S3_BUCKET="mypypi-files"
MYPYPI_S3_ACCESS_KEY="<AWS access key>"
MYPYPI_S3_SECRET_KEY="<AWS secret key>"
MYPYPI_S3_PUBLIC=true

MYPYPI_DATABASE_DRIVER="mysql"
MYPYPI_DATABASE_NAME="mypypi"
MYPYPI_DATABASE_USER="mypypi"
MYPYPI_DATABASE_PASSWORD="<password>"
MYPYPI_DATABASE_HOST="<host>"
MYPYPI_DATABASE_PORT=3306
```

## Maintenance

If you want to delete some old files that are taking up space, you can run

```bash
python prune.py <days> --dry-run
```

inside the container. This will tell you how many files have not been deleted
for X number of days, and will be deleted once you remove `--dry-run`. Remove the
`--dry-run` flag to execute.
