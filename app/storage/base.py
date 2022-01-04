import abc
from typing import List, Optional, Tuple


class BaseStorage(abc.ABC):
    def get_url_cache(self, url: str) -> Optional[Tuple[int, bytes, str]]:
        """
        Return the status code, content, and headers of a url cache.
        Return None if not found.
        """
        raise NotImplementedError

    def set_url_cache(
        self, url: str, status_code: int, contet: bytes, headers: str
    ) -> None:
        """
        Create a url cache.
        """
        raise NotImplementedError

    def del_url_cache(self, url: str) -> None:
        """
        Delete a url cache.
        """
        raise NotImplementedError

    def is_url_cache_valid(self, url: str, max_age: int) -> bool:
        """
        Return whether or not a url cache is still valid.
        """
        raise NotImplementedError

    def get_file_url_from_hash(self, hash_: str) -> Optional[str]:
        """
        Return the url for a hash.
        Return None if not found.
        """
        raise NotImplementedError

    def get_hash_from_file_url(self, url: str) -> Optional[str]:
        """
        Return the hash for a url.
        Return None if not found.
        """
        raise NotImplementedError

    def get_or_create_file_url_hash(self, url: str) -> str:
        """
        Return the generated hash of a url.
        """
        raise NotImplementedError

    def create_file_url_hashes(self, urls: List[str]) -> List[str]:
        """
        Return the generated hash of multiple urls.
        """
        raise NotImplementedError

    def update_file_url_last_downloaded_time(self, url: str) -> None:
        """
        Update the last download time of a url.
        """
        raise NotImplementedError

    def delete_older_than_days(self, days: int) -> None:
        """
        Delete all urls that were downloaded more than days ago.
        """
        raise NotImplementedError
