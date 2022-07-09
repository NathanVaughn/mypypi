# MyPyPi

This is a simple pull-through cache for any Python package index or NPM registry.
It is meant as a way to have a local cache of packages in case the source package
index is down, speed up CI/CD, etc. This is NOT a way to distribute custom packages
interally. For that, I recommend more advanced solutions like Artifactory,
Azure Artifacts, etc.

## What this is

-   A very dumb package registry server
-   A way to cache package files
-   A way to prevent upstream server outages affecting your builds
-   A very quick hobby project

## What this is NOT

-   A way to publish packages internally
-   A package registry server with authentication
-   Particualry fast. Basically guaranteed to be slower than the source package index
-   A way to prevent yanked packages or versions from breaking your builds
    (package files are saved, but the package pages with the version listings are taken
    directly from the upstream source)

Additionally, in "npm" mode, only basic package installs/updates are supported.
`npm audit` and other `npm` commands like that are not supported.

## Setup

MyPyPi requires 3 services to be running:

1. Redis server: Stores persistent data
2. MyPyPi server: Answers requests on port 80
3. MyPyPi worker: Runs background tasks

As an example, see the [`docker-compose.yml`](docker-compose.yml) file.

### Common Environment Variables

These environment variables should be set to the same value for BOTH
the server and worker.

| Name                            | Description                                                                                                                                                                                                                                             | Default                  |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| `MYPYPI_PACKAGE_TYPE`           | Whether to host `pypi` or `npm` packages.                                                                                                                                                                                                               | `pypi`                   |
| `MYPYPI_UPSTREAM_USERNAME`      | HTTP basic auth username for upstream.                                                                                                                                                                                                                  |                          |
| `MYPYPI_UPSTREAM_PASSWORD`      | HTTP basic auth password for upstream.                                                                                                                                                                                                                  |                          |
| `MYPYPI_FILE_STORAGE_DRIVER`    | What file storage driver to use. Valid values are `local` or `s3`.                                                                                                                                                                                      | `local`                  |
| `MYPYPI_FILE_STORAGE_DIRECTORY` | If using the local file storage, what directory relative to store package files in. Make sure this directory is mounted in both the worker and server.                                                                                                  | `data/files`             |
| `MYPYPI_S3_BUCKET`              | If using S3 file storage, what bucket to store files in.                                                                                                                                                                                                |                          |
| `MYPYPI_S3_PREFIX`              | If using S3 file storage, an optional prefix to use.                                                                                                                                                                                                    |                          |
| `MYPYPI_S3_ACCESS_KEY`          | If using S3 file storage, the access key to use.                                                                                                                                                                                                        |                          |
| `MYPYPI_S3_SECRET_KEY`          | If using S3 file storage, the secret key to use. This should have permission to create pre-signed URLs.                                                                                                                                                 |                          |
| `MYPYPI_S3_ENDPOINT_URL`        | If using S3 file storage, alternative endpoint URL (not needed if using AWS). Protocol (`https://`) is required.                                                                                                                                        |                          |
| `MYPYPI_S3_REGION`              | If using S3 file storage, region to use (may be required depending on provider).                                                                                                                                                                        |                          |
| `MYPYPI_S3_PUBLIC`              | If using S3 file storage, whether or not the bucket is public. If it is, and this variable is set to `true`, then this will remove URL query parameters to help facilitate caching by `pip`, along with internally more aggressively caching responses. | `false`                  |
| `MYPYPI_S3_KEY_TTL`             | If using S3 file storage, how long to generate pre-signed URLs for, in seconds. No effect if `MYPYPI_S3_PUBLIC` is `true`. This must be greater than 60.                                                                                                | `600`                    |
| `MYPYPI_REDIS_URL`              | Redis connection string.                                                                                                                                                                                                                                | `redis://localhost:6379` |
| `MYPYPI_REDIS_PREFIX`           | Redis key prefix.                                                                                                                                                                                                                                       | `mypypi`                 |

### Server Environment Variables

These environment variables are specific to the server.

| Name                     | Description                                                                                                                                                                                                                                                                                                                                            | Default                                                                         |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------- |
| `WORKERS`                | How many server workers to spawn to answer requests                                                                                                                                                                                                                                                                                                    | `8`                                                                             |
| `MYPYPI_MODE`            | Whether to run the application in `server` or `worker` mode.                                                                                                                                                                                                                                                                                           | `server`                                                                        |
| `MYPYPI_UPSTREAM_URL`    | URL of the source package index/registry. Do NOT include the trailing `/simple`.                                                                                                                                                                                                                                                                       | `https://pypi.org` in "pypi" mode or `https://registry.npmjs.org` in "npm" mode |
| `MYPYPI_UPSTREAM_STRICT` | If `false`, will redirect requests to the upstream file source while a file is being cached the first time. If set to `true`, will return 503 until the file has been cached. `pip` usually handles this okay, but for large files, this may cause timeouts. This is good if you decided to completely block the upstream source at the network level. | `false`                                                                         |
| `MYPYPI_CACHE_TIME`      | How long to cache upstream package information for, in seconds, before the upstream source is checked again. This will effectively limit how long it takes for new versions to appear.                                                                                                                                                                 | `300`                                                                           |

## Example Configs

### Simple

```python
MYPYPI_PACKAGE_TYPE="pypi"
MYPYPI_UPSTREAM_URL="https://pypi.org"

MYPYPI_CACHE_TIME=300

MYPYPI_DATA_DIRECTORY="data"
MYPYPI_FILE_STORAGE_DRIVER="local"
MYPYPI_FILE_STORAGE_DIRECTORY="files"

MYPYPI_REDIS_URL="redis://localhost:6379"
```

### (More) Production Grade

```python
MYPYPI_PACKAGE_TYPE="pypi"
MYPYPI_UPSTREAM_URL="https://pypi.org"

MYPYPI_REDIS_URL="redis://<host>:6379"
MYPYPI_REDIS_PREFIX="mypypi"
MYPYPI_CACHE_TIME=300

MYPYPI_FILE_STORAGE_DRIVER="s3"
MYPYPI_S3_BUCKET="mypypi-files"
MYPYPI_S3_ACCESS_KEY="<AWS access key>"
MYPYPI_S3_SECRET_KEY="<AWS secret key>"
MYPYPI_S3_PUBLIC=true
```
