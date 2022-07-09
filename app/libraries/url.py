import os
from typing import Tuple
from urllib.parse import urlparse

import packaging.utils


def url_filename(url: str, keep_anchor: bool = False) -> str:
    """
    Given a url, return the filename. Optionally keep the anchor.
    """
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path)

    if keep_anchor:
        filename = f"{filename}#{parsed.fragment}"

    return filename


def parse_npm_file_url(url: str) -> Tuple[str, str]:
    """
    Given a file url, return the package name and filename.
    """
    # for example:
    # https://registry.npmjs.org/@zzzen/pyright-internal/-/pyright-internal-1.1.254.tgz
    # https://registry.npmjs.org/pyright/-/pyright-1.1.254.tgz
    # https://registry.npmjs.org/-/-/--0.0.1.tgz

    # parse the url
    parsed = urlparse(url)

    # grab filename off end
    filename = os.path.basename(parsed.path)

    # get the rest of the url
    temp_path = parsed.path.removesuffix(filename)

    # remove the seperator /-/
    package = temp_path.removesuffix("/-/")

    return package, filename


def parse_pypi_file_url(url: str) -> Tuple[str, str]:
    """
    Given a file url, return the package name and version.
    """
    filename = url_filename(url)

    try:
        if filename.endswith(".whl"):
            name, version, _, _ = packaging.utils.parse_wheel_filename(filename)
        else:
            name, version = packaging.utils.parse_sdist_filename(filename)
    except (
        packaging.utils.InvalidSdistFilename,
        packaging.utils.InvalidWheelFilename,
    ) as e:
        raise ValueError(f"Invalid filename: {filename}") from e

    return name, str(version)
