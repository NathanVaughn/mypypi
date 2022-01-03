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

    def get_url_token(self, url: str) -> Optional[str]:
        """
        Return the token of a url.
        Return None if not found.
        """
        raise NotImplementedError

    def set_url_token(self, url: str) -> str:
        """
        Return the generated token of a url.
        """
        raise NotImplementedError

    def set_url_tokens(self, urls: List[str]) -> List[str]:
        """
        Return the generated token of multiple urls.
        """
        raise NotImplementedError
