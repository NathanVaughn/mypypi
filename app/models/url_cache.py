from typing import List, Tuple, TypedDict


class URLCache(TypedDict):
    status_code: int
    content: str
    headers: List[Tuple[str, str]]
