from __future__ import annotations

import time
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from app.files.base import BaseFiles
    from app.storage.base import BaseStorage


class Downloader:
    def __init__(self, storage_backend: BaseStorage, file_backend: BaseFiles) -> None:
        self.storage_backend = storage_backend
        self.file_backend = file_backend

        logger.debug("Initializing Downloader")

    def execute(self) -> None:
        """
        Check the download task queue for any tasks that need to be executed.
        """
        url = self.storage_backend.get_oldest_url_download_task()
        if url is None:
            # if there's no task, sleep for a bit
            time.sleep(1)
            return

        try:
            self.file_backend.save(url)
        except Exception:
            logger.exception(f"Failed to save {url}")
        finally:
            self.storage_backend.del_url_download_task(url)

    def run(self) -> None:
        """
        Run the Downloader infinitely. Should be started in a seperate thread.
        """
        while True:
            self.execute()
