import os
import secrets
from typing import List, Optional, Tuple

import peewee as pw

from app.storage.base import BaseStorage

db = pw.SqliteDatabase(None)


class BaseModel(pw.Model):
    class Meta:
        database = db


# table to hold our tokens and the urls they are associated with
class URLToken(BaseModel):
    url = pw.TextField(unique=True)
    token = pw.TextField(unique=True)


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
        db.create_tables([URLToken, URLCache])

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

    def get_url_token(self, url: str) -> Optional[str]:
        # get the token of a url
        url_token = URLToken.get_or_none(URLToken.url == url)

        if url_token is None:
            return None

        return url_token.token

    def set_url_token(self, url: str) -> str:
        # create a token for a url
        token = secrets.token_hex(64)
        URLToken.create(url=url, token=token)

        return token

    def set_url_tokens(self, urls: List[str]) -> List[str]:
        urltokens = [URLToken(url=url, token=secrets.token_hex(64)) for url in urls]
        with db.atomic():
            URLToken.bulk_create(urltokens, batch_size=100)

        return [str(urltoken.token) for urltoken in urltokens]
