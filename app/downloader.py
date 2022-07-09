from __future__ import annotations

import time
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from app.database import Database
    from app.files.base import BaseFiles


class Downloader:
    def __init__(self, database: Database, files_backend: BaseFiles) -> None:
        self.database = database
        self.files_backend = files_backend

        logger.debug("Initializing Downloader")

    def execute(self) -> None:
        """
        Check the download task queue for any tasks that need to be executed.
        """
        url = self.database.get_file_download_job()
        if url is None:
            # if there's no task, sleep for a bit
            time.sleep(1)
            return

        try:
            self.files_backend.save(url)
        except Exception:
            logger.exception(f"Failed to save {url}")
        finally:
            self.database.del_file_download_job(url)

    def run(self) -> None:
        """
        Run the Downloader infinitely.
        """
        while True:
            try:
                self.execute()
            except Exception as e:
                logger.exception("Downloader crashed")
                raise e
