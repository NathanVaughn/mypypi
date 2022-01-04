import datetime
import os
from typing import List, Optional, Tuple

import peewee as pw

import app.libraries.hash
from app.storage.base import BaseStorage

db = pw.SqliteDatabase(None)


class BaseModel(pw.Model):
    class Meta:
        database = db


# table to hold url caches
class URLCache(BaseModel):
    url = pw.TextField(unique=True)
    status_code = pw.IntegerField()
    headers = pw.TextField()  # stored as json
    content = pw.BlobField()
    time_created = pw.DateTimeField(default=datetime.datetime.now)


# table to hold our hashes and the urls they are associated with
class FileURL(BaseModel):
    url = pw.TextField(unique=True)
    hash_ = pw.TextField(unique=True)
    time_last_downloaded = pw.DateTimeField(null=True)


class SQLStorage(BaseStorage):
    def __init__(self, file_path: str) -> None:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        db.init(file_path)
        db.create_tables([URLCache, FileURL])

    # ================================================================
    # URL Cache
    # ================================================================

    def _get_url_cache_obj(self, url: str) -> Optional[URLCache]:
        # get a URLCache object
        return URLCache.get_or_none(URLCache.url == url)

    def get_url_cache(self, url: str) -> Optional[Tuple[int, bytes, str]]:
        # get URLCache properties, or return None
        url_cache = self._get_url_cache_obj(url)

        if url_cache is None:
            return None

        return int(url_cache.status_code), bytes(url_cache.content), str(url_cache.headers)  # type: ignore

    def del_url_cache(self, url: str) -> None:
        # delete an existing url cache
        url_cache = self._get_url_cache_obj(url)

        if url_cache is not None:
            url_cache.delete_instance()

    def set_url_cache(
        self, url: str, status_code: int, content: bytes, headers: str
    ) -> None:
        # delete url cache if it already exists
        if self.get_url_cache(url) is None:
            self.del_url_cache(url)

        URLCache.create(
            url=url,
            status_code=status_code,
            headers=headers,
            content=content,
        )

    def is_url_cache_valid(self, url: str, max_age: int) -> bool:
        # check if a url cache is still valid
        url_cache = self._get_url_cache_obj(url)

        if url_cache is None:
            return False

        return (pw.datetime.datetime.now() - url_cache.time_created).total_seconds() < max_age  # type: ignore

    # ================================================================
    # File URL
    # ================================================================

    def get_file_url_from_hash(self, hash_: str) -> Optional[str]:
        # get url from hash
        file_url = FileURL.get_or_none(FileURL.hash_ == hash_)

        if file_url is None:
            return None

        return file_url.url

    def get_hash_from_file_url(self, url: str) -> Optional[str]:
        # get hash from url
        file_url = FileURL.get_or_none(FileURL.url == url)

        if file_url is None:
            return None

        return file_url.hash_

    def get_or_create_file_url_hash(self, url: str) -> str:
        # get or create an entry for the url
        hash_ = app.libraries.hash.sha256_string(url)

        if self.get_file_url_from_hash(hash_) is None:
            FileURL.create(url=url, hash_=hash_)

        return hash_

    def create_file_url_hashes(self, urls: List[str]) -> List[str]:
        # generate list of objects
        file_urls = [
            FileURL(url=url, hash_=app.libraries.hash.sha256_string(url))
            for url in urls
        ]
        # bulk create
        with db.atomic():
            FileURL.bulk_create(file_urls, batch_size=100)

        return [str(file_url.hash_) for file_url in file_urls]

    def update_file_url_last_downloaded_time(self, url: str) -> None:
        # update the last downloaded time for the url
        file_url = FileURL.get_or_none(FileURL.url == url)

        if file_url is not None:
            file_url.time_last_downloaded = datetime.datetime.now()
            file_url.save()

    # ================================================================
    # Prune
    # ================================================================
    def delete_older_than_days(self, days: int) -> None:
        # this is imported here to avoid circular imports
        # very infrequently used, so not too big of a deal
        from app.main import file_backend  # noqa

        file_urls: List[FileURL] = FileURL.select().where(FileURL.time_last_downloaded < datetime.datetime.now() - datetime.timedelta(days=days))  # type: ignore

        for file_url in file_urls:
            file_backend.delete(str(file_url.url))
            file_url.delete_instance()
