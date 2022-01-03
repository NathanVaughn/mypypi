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

    def get_url_from_hash(self, hash_: str) -> Optional[str]:
        """
        Return the url for a hash.
        Return None if not found.
        """
        raise NotImplementedError

    def set_url_hash(self, url: str) -> str:
        """
        Return the generated hash of a url.
        """
        raise NotImplementedError

    def set_url_hashes(self, urls: List[str]) -> List[str]:
        """
        Return the generated hash of multiple urls.
        """
        raise NotImplementedError
