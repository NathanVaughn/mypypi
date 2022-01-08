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
        Return the url for a hash. Return None if not found.
        """
        raise NotImplementedError

    def get_or_create_file_url_hashes(self, urls: List[str]) -> List[str]:
        """
        Get or create the hash for a list of urls.
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

    def check_url_task(self, url: str) -> bool:
        """
        Return if a task for the given url exists
        """
        raise NotImplementedError

    def add_url_task(self, url: str) -> None:
        """
        Add a task record for the url.
        """
        raise NotImplementedError

    def del_url_task(self, url: str) -> None:
        """
        Delete the task record for the url.
        """
        raise NotImplementedError
