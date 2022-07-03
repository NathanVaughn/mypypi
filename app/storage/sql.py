import datetime
from typing import List, Optional, Tuple

import peewee as pw
from loguru import logger

from app.libraries.url import generate_url_key
from app.storage.base import BaseStorage

db = pw.DatabaseProxy()


class BaseModel(pw.Model):
    class Meta:
        database = db


# while SQLite and Postgres can store up to 1GB in the blob field,
# MySQL is capped at a whopping 64 KB. Thus, maintain a table of multiple
# blob chunks that can be reconstructed.
class BlobChunk(BaseModel):
    key = pw.TextField()
    order = pw.IntegerField()
    content = pw.BlobField()


# table to hold url caches
class URLCache(BaseModel):
    url = pw.TextField(unique=True)
    status_code = pw.IntegerField()
    headers = pw.TextField()  # stored as json
    time_created = pw.DateTimeField(default=datetime.datetime.now)


# table to hold our hashes and the urls they are associated with
class FileURL(BaseModel):
    url = pw.TextField(unique=True)
    key = pw.TextField(unique=True)
    time_last_downloaded = pw.DateTimeField(null=True)
    download_count = pw.IntegerField(default=0)


# table to hold in-progress downloads
class URLTask(BaseModel):
    url = pw.TextField(unique=True)
    time_created = pw.DateTimeField(default=datetime.datetime.now)


class SQLStorage(BaseStorage):
    def __init__(self, database: pw.Database) -> None:
        db.initialize(database)
        db.create_tables([BlobChunk, URLCache, FileURL, URLTask])

    # ================================================================
    # URL Cache
    # ================================================================

    def _get_url_cache_obj(self, url: str) -> Optional[URLCache]:
        # get a URLCache object
        logger.debug(f"Getting URL Cache object for {url}")
        result = URLCache.get_or_none(URLCache.url == url)
        logger.debug(f"Result: {bool(result)}")

        return result

    def get_url_cache(self, url: str) -> Optional[Tuple[int, bytes, str]]:
        # get URLCache properties, or return None
        logger.debug(f"Getting url cache for {url}")

        url_cache = self._get_url_cache_obj(url)

        if url_cache is None:
            logger.debug(f"No url cache found for {url}")
            return None

        # get the blobs
        logger.debug(f"Reconstructing blobs for {url}")
        chunks = BlobChunk.select().where(BlobChunk.key == url).order_by(BlobChunk.order)  # type: ignore
        content = b"".join([chunk.content for chunk in chunks])

        return int(url_cache.status_code), bytes(content), str(url_cache.headers)  # type: ignore

    def del_url_cache(self, url: str) -> None:
        # delete an existing url cache
        logger.debug(f"Deleting url cache for {url}")

        url_cache = self._get_url_cache_obj(url)

        if url_cache is not None:
            logger.debug(f"Url cache found for {url}, deleting")
            url_cache.delete_instance()

        # delete the blobs
        logger.debug(f"Deleting blobs for {url}")
        BlobChunk.delete().where(BlobChunk.key == url).execute()  # type: ignore

    def set_url_cache(
        self, url: str, status_code: int, content: bytes, headers: str
    ) -> None:
        logger.debug(f"Setting url cache for {url}")

        # delete url cache if it already exists
        if self._get_url_cache_obj(url) is not None:
            logger.debug(f"Deleting existing url cache for {url}")
            self.del_url_cache(url)

        URLCache.create(
            url=url,
            status_code=status_code,
            headers=headers,
        )

        logger.debug(f"Creating blobs for {url}")

        # split the return data into chunks
        chunk_size = 65535 - 1000  # fudge factor
        data_chunks = [
            content[i : i + chunk_size] for i in range(0, len(content), chunk_size)
        ]
        chunks = [
            BlobChunk(key=url, order=i, content=chunk)
            for i, chunk in enumerate(data_chunks)
        ]

        # bulk create
        with db.atomic():
            BlobChunk.bulk_create(chunks, batch_size=100)

        logger.debug(f"Url cache for {url} set")

    def is_url_cache_valid(self, url: str, max_age: int) -> bool:
        logger.debug(f"Checking if url cache for {url} is valid")

        # check if a url cache is still valid
        url_cache = self._get_url_cache_obj(url)

        if url_cache is None:
            return False

        result = (pw.datetime.datetime.now() - url_cache.time_created).total_seconds() < max_age  # type: ignore
        logger.debug(f"Result: {result}")

        return result

    # ================================================================
    # File URL
    # ================================================================

    def get_file_url_from_key(self, key: str) -> Optional[str]:
        # get url from hash
        logger.debug(f"Getting file url from key {key}")
        file_url = FileURL.get_or_none(FileURL.key == key)

        if file_url is None:
            return None

        return file_url.url

    def get_or_create_file_url_keys(self, urls: List[str]) -> List[str]:
        logger.debug("Getting bulk list of keys")

        # preprocess URLs to remove anchors
        urls = [url.split("#")[0] for url in urls]

        # first, get urls that already exist
        file_url_objs: List[FileURL] = FileURL.select(FileURL.url).where(FileURL.url.in_(urls)).execute()  # type: ignore
        file_url_urls = [file_url.url for file_url in file_url_objs]

        # create new file url entries for the missing urls
        new_file_urls = [
            FileURL(url=url, key=generate_url_key(url))
            for url in urls
            if url not in file_url_urls
        ]

        # bulk create
        with db.atomic():
            FileURL.bulk_create(new_file_urls, batch_size=100)

        # now, get the keys for all the urls
        return [generate_url_key(url) for url in urls]

    def update_file_url_last_downloaded_time(self, url: str) -> None:
        logger.debug(f"Updating last downloaded time for {url}")

        # update the last downloaded time for the url
        file_url = FileURL.get_or_none(FileURL.url == url)

        if file_url is not None:
            file_url.download_count += 1
            file_url.time_last_downloaded = datetime.datetime.now()
            file_url.save()

    # ================================================================
    # Downloads
    # ================================================================

    def check_url_task(self, url: str) -> bool:
        # get a download task
        logger.debug(f"Checking if task for {url} exists")
        result = bool(URLTask.get_or_none(URLTask.url == url))
        logger.debug(f"Result: {result}")

        return result

    def add_url_task(self, url: str) -> None:
        logger.debug(f"Creating task for {url}")
        URLTask.create(url=url)

    def del_url_task(self, url: str) -> None:
        # delete a url task
        logger.debug(f"Deleting task for {url}")
        task = URLTask.get(URLTask.url == url)
        task.delete_instance()

    # ================================================================
    # Prune
    # ================================================================
    def delete_older_than_days(self, days: int, dry_run: bool = False) -> List[str]:
        # this is imported here to avoid circular imports
        # very infrequently used, so not too big of a deal
        from app.main import file_backend  # noqa

        file_urls: List[FileURL] = FileURL.select().where(FileURL.time_last_downloaded < datetime.datetime.now() - datetime.timedelta(days=days))  # type: ignore
        file_urls_urls = [str(file_url.url) for file_url in file_urls]

        if not dry_run:
            for file_url in file_urls:
                file_backend.delete(str(file_url.url))
                file_url.delete_instance()

        return file_urls_urls
