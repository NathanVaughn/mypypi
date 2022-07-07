# MyPyPi

This is a simple pull-through cache for any Python package index or NPM registry.
It is meant as a way to have a local cache of packages in case the source package
index is down, speed up CI/CD, etc. This is NOT a way to distribute custom packages
interally. For that, I recommend more advanced solutions like Artifactory,
Azure Artifacts, etc.

Additionally, there is no concept of user accounts or authentication. If desired,
this is up to you to provide via a reverse proxy, network rules, etc.

In "npm" mode, only basic package installs/updates are supported.
`npm audit` and other `npm` commands like that are not supported.

## Setup

All environment variables begin with `MYPYPI_`.

| Name                            | Description                                                                                                                                                                                                                                                                                                                                            | Default                                                                         |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------- |
| `MYPYPI_MODE`                   | Whether to run the application in `pypi` or `npm` mode.                                                                                                                                                                                                                                                                                                | `pypi`                                                                          |
| `MYPYPI_UPSTREAM_URL`           | URL of the source package index/registry. Do NOT include the trailing `/simple`.                                                                                                                                                                                                                                                                       | `https://pypi.org` in "pypi" mode or `https://registry.npmjs.org` in "npm" mode |
| `MYPYPI_UPSTREAM_USERNAME`      | HTTP basic auth username for upstream.                                                                                                                                                                                                                                                                                                                 |                                                                                 |
| `MYPYPI_UPSTREAM_PASSWORD`      | HTTP basic auth password for upstream.                                                                                                                                                                                                                                                                                                                 |                                                                                 |
| `MYPYPI_UPSTREAM_STRICT`        | If `false`, will redirect requests to the upstream file source while a file is being cached the first time. If set to `true`, will return 503 until the file has been cached. `pip` usually handles this okay, but for large files, this may cause timeouts. This is good if you decided to completely block the upstream source at the network level. | `false`                                                                         |
| `MYPYPI_CACHE_TIME`             | How long to cache upstream package versions, in seconds                                                                                                                                                                                                                                                                                                | `1800`                                                                          |
| `MYPYPI_DATA_DIRECTORY`         | Directory to store persistent data in. Can be absolute or relative to working directory                                                                                                                                                                                                                                                                | `data`                                                                          |
| `MYPYPI_FILE_STORAGE_DRIVER`    | What file storage driver to use. Valid values are `local` or `s3`                                                                                                                                                                                                                                                                                      | `local`                                                                         |
| `MYPYPI_FILE_STORAGE_DIRECTORY` | If using the local file storage, what directory relative to `DATA_DIRECTORY` to store package files in                                                                                                                                                                                                                                                 | `files`                                                                         |
| `MYPYPI_S3_BUCKET`              | If using S3 file storage, what bucket to store files in                                                                                                                                                                                                                                                                                                |                                                                                 |
| `MYPYPI_S3_PREFIX`              | If using S3 file storage, an optional prefix to use                                                                                                                                                                                                                                                                                                    |                                                                                 |
| `MYPYPI_S3_ACCESS_KEY`          | If using S3 file storage, the access key to use                                                                                                                                                                                                                                                                                                        |                                                                                 |
| `MYPYPI_S3_SECRET_KEY`          | If using S3 file storage, the secret key to use. If the bucket is not public, this should have permission to create signed URLS                                                                                                                                                                                                                        |                                                                                 |
| `MYPYPI_S3_ENDPOINT_URL`        | If using S3 file storage, alternative endpoint URL (not needed if using AWS). Protocol (`https://`) is required.                                                                                                                                                                                                                                       |                                                                                 |
| `MYPYPI_S3_REGION`              | If using S3 file storage, region to use (may be required depending on provider)                                                                                                                                                                                                                                                                        |                                                                                 |
| `MYPYPI_S3_PUBLIC`              | If using S3 file storage, whether or not the bucket is public. If it is, and this variable is set to `true`, then this will remove URL query parameters to help facilitate caching by `pip`.                                                                                                                                                           | `false`                                                                         |
| `MYPYPI_REDIS_URL`              | Redis connection string                                                                                                                                                                                                                                                                                                                                | `redis://localhost:6379`                                                        |
| `MYPYPI_REDIS_PREFIX`           | Redis prefix                                                                                                                                                                                                                                                                                                                                           | `mypypi`                                                                        |

## Example Configs

### Simple

```python
MYPYPI_MODE="pypi"
MYPYPI_UPSTREAM_URL="https://pypi.org"

MYPYPI_CACHE_DEFAULT_TIMEOUT=1800

MYPYPI_DATA_DIRECTORY="data"
MYPYPI_FILE_STORAGE_DRIVER="local"
MYPYPI_FILE_STORAGE_DIRECTORY="files"

MYPYPI_REDIS_URL="redis://localhost:6379"
```

### (More) Production Grade

```python
MYPYPI_MODE="pypi"
MYPYPI_UPSTREAM_URL="https://pypi.org"

MYPYPI_REDIS_URL="redis://<host>:6379"
MYPYPI_REDIS_PREFIX="mypypi"
MYPYPI_CACHE_TIME=1800

MYPYPI_FILE_STORAGE_DRIVER="s3"
MYPYPI_S3_BUCKET="mypypi-files"
MYPYPI_S3_ACCESS_KEY="<AWS access key>"
MYPYPI_S3_SECRET_KEY="<AWS secret key>"
MYPYPI_S3_PUBLIC=true
```
