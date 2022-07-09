import datetime
from typing import List, Optional, Tuple

import orjson
from redis import Redis

from app.main import flask_app
from app.models.url_cache import URLCache


class Database:
    def __init__(self, redis_client: Redis) -> None:
        self.redis_client = redis_client

        self._redis_prefix = (
            f"{flask_app.config['REDIS_PREFIX']}:{flask_app.config['PACKAGE_TYPE']}"
        )
        self._data_sep = "data"
        self._time_sep = "time"
        self._file_url_sep = "file_url"
        self._file_download_queue_name = "file_download_queue"

    @staticmethod
    def process_key(key: str) -> str:
        """
        Process a Redis key to replace colons with something else.
        """
        return key.replace(":", "_")

    # url cache

    def set_url_cache(self, url: str, data: URLCache) -> None:
        """
        Set URL cache data to the redis cache.
        """
        # record the actual data
        self.redis_client.set(
            f"{self._redis_prefix}:{self._data_sep}:{self.process_key(url)}",
            orjson.dumps(data).decode("utf-8"),
        )
        # record the time of the data
        self.redis_client.set(
            f"{self._redis_prefix}:{self._time_sep}:{self.process_key(url)}",
            datetime.datetime.now().isoformat(),
        )

    def get_url_cache(
        self, url: str
    ) -> Tuple[Optional[datetime.datetime], Optional[URLCache]]:
        """
        Get URL cache data from the redis cache.
        """
        data = self.redis_client.get(
            f"{self._redis_prefix}:{self._data_sep}:{self.process_key(url)}"
        )
        if data is None:
            return (None, None)

        timestamp = self.redis_client.get(
            f"{self._redis_prefix}:{self._time_sep}:{self.process_key(url)}"
        )
        if timestamp is None:
            return (None, None)

        return datetime.datetime.fromisoformat(timestamp), orjson.loads(data)

    # file download jobs

    def add_file_download_job(self, url: str) -> None:
        """
        Add a file download job to the redis queue.
        """
        self.redis_client.rpush(
            f"{self._redis_prefix}:{self._file_download_queue_name}", url
        )

    def check_file_download_job(self, url: str) -> bool:
        """
        Check if a file download job is in the redis queue.
        """
        return (
            self.redis_client.lrem(
                f"{self._redis_prefix}:{self._file_download_queue_name}", 0, url
            )
            > 0
        )

    def get_file_download_job(self) -> Optional[str]:
        """
        Get a file download job from the redis queue.
        """
        return self.redis_client.lpop(
            f"{self._redis_prefix}:{self._file_download_queue_name}"
        )

    def del_file_download_job(self, url: str) -> None:
        """
        Delete a file download job from the redis queue.
        """
        self.redis_client.lrem(
            f"{self._redis_prefix}:{self._file_download_queue_name}", 0, url
        )

    # file url keys

    def add_file_url_key(self, filekey: str, url: str) -> None:
        """
        Add entry of a key that we can use to look up the source file URL later.
        """
        self.redis_client.set(
            f"{self._redis_prefix}:{self._file_url_sep}:{self.process_key(filekey)}",
            url,
        )

    def bulk_add_file_url_keys(self, entries: List[Tuple[str, str]]) -> None:
        """
        Bulk add tuples of file key and URL to redis.
        """
        pipe = self.redis_client.pipeline()
        for filekey, url in entries:
            pipe.set(
                f"{self._redis_prefix}:{self._file_url_sep}:{self.process_key(filekey)}",
                url,
            )

        pipe.execute()

    def get_file_url_from_key(self, filekey: str) -> Optional[str]:
        """
        Get the source file URL from a key.
        """
        return self.redis_client.get(
            f"{self._redis_prefix}:{self._file_url_sep}:{self.process_key(filekey)}"
        )
