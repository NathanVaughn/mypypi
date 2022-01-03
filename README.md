# MyPyPi

This is a pull-through cache for any Python package index. It is meant as a way
to have a local cache of packages in case the source package index is down, speed
up CI/CD, etc. This is NOT a way to distribute to custom packages interally.
For that, I recommend more advanced solutions like Artifactory.

## Setup

All environment variables should be prefixed with `MYPYPI_`.

| Name                    | Description                                                                                            | Default            |
| ----------------------- | ------------------------------------------------------------------------------------------------------ | ------------------ |
| `UPSTREAM_URL`          | URL of the source package index. Do NOT include the trailing `/simple`.                                | `https://pypi.org` |
| `UPSTREAM_TTL`          | How long to cache upstream package versions, in seconds                                                | `1800`             |
| `DATA_DIRECTORY`        | Directory to store persistent data in. Can be absolute or relative to working directory                | `data`             |
| `FILE_STORAGE`          | What file storage backend to use. Valid values are `local` or `s3`                                     | `local`            |
| `LOCAL_FILES_DIRECTORY` | If using the local file storage, what directory relative to `DATA_DIRECTORY` to store package files in | `files`            |
| `S3_BUCKET`             | If using S3 file storage, what bucket to store files in                                                |                    |
| `S3_ACCESS_KEY`         | If using S3 file storage, the access key to use                                                        |                    |
| `S3_SECRET_KEY`         | If using S3 file storage, the secret key to use                                                        |                    |
| `S3_ENDPOINT_URL`       | If using S3 file storage, alternative endpoint URL (not needed if using AWS)                           |                    |
| `S3_REGION`             | If using S3 file storage, region to use (may be required depending on provider)                        |                    |
| `SQLITE_FILENAME`       | SQLite file relative to `DATA_DIRECTORY` to keep the database                                          | `database.sqlite`  |
