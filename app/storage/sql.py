import os
from typing import List, Optional, Tuple

import peewee as pw

import app.libraries.hash
from app.storage.base import BaseStorage

db = pw.SqliteDatabase(None)


class BaseModel(pw.Model):
    class Meta:
        database = db


# table to hold our hashes and the urls they are associated with
class URLHash(BaseModel):
    url = pw.TextField(unique=True)
    hash_ = pw.TextField(unique=True)


# table to hold url caches
class URLCache(BaseModel):
    url = pw.TextField(unique=True)
    status_code = pw.IntegerField()
    headers = pw.TextField()  # stored as json
    content = pw.BlobField()
    time_created = pw.DateTimeField(default=pw.datetime.datetime.now)


class SQLStorage(BaseStorage):
    def __init__(self, file_path: str) -> None:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        db.init(file_path)
        db.create_tables([URLHash, URLCache])

    def _get(self, url: str) -> Optional[URLCache]:
        # get a URLCache object
        return URLCache.get_or_none(URLCache.url == url)

    def get_url_cache(self, url: str) -> Optional[Tuple[int, bytes, str]]:
        # get URLCache properties, or return None
        url_cache = self._get(url)

        if url_cache is None:
            return None

        return int(url_cache.status_code), bytes(url_cache.content), str(url_cache.headers)  # type: ignore

    def set_url_cache(
        self, url: str, status_code: int, content: bytes, headers: str
    ) -> None:
        URLCache.create(
            url=url,
            status_code=status_code,
            headers=headers,
            content=content,
        )

    def del_url_cache(self, url: str) -> None:
        # delete an existing url cache
        url_cache = self._get(url)

        if url_cache is not None:
            url_cache.delete_instance()

    def is_url_cache_valid(self, url: str, max_age: int) -> bool:
        # check if a url cache is still valid
        url_cache = self._get(url)

        if url_cache is None:
            return False

        return (pw.datetime.datetime.now() - url_cache.time_created).total_seconds() < max_age  # type: ignore

    def get_url_from_hash(self, hash_: str) -> Optional[str]:
        # get url from hash
        url_hash = URLHash.get_or_none(URLHash.hash_ == hash_)

        if url_hash is None:
            return None

        return url_hash.url

    def set_url_hash(self, url: str) -> str:
        # create an entry for the url
        hash_ = app.libraries.hash.sha256_string(url)

        if self.get_url_from_hash(hash_) is None:
            URLHash.create(url=url, hash_=hash_)

        return hash_

    def set_url_hashes(self, urls: List[str]) -> List[str]:
        url_hashes = [
            URLHash(url=url, hash_=app.libraries.hash.sha256_string(url))
            for url in urls
        ]
        with db.atomic():
            URLHash.bulk_create(url_hashes, batch_size=100)

        return [str(url_hash.hash_) for url_hash in url_hashes]
