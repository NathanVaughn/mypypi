import functools
import hashlib


@functools.lru_cache(maxsize=None)
def sha256_string(content: str) -> str:
    """
    Hash a string using SHA256. Cache results for repeated use.
    """
    h = hashlib.sha256()
    h.update(content.encode("utf-8"))
    return h.hexdigest()
