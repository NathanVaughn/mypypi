import http
from urllib.parse import unquote

import bs4
import cachetools.func
import flask

import app.libraries.url
from app.main import database_backend, flask_app, proxy

url_prefix = "simple"
simple_bp = flask.Blueprint("simple", __name__, url_prefix=f"/{url_prefix}")


@cachetools.func.ttl_cache(maxsize=None, ttl=flask_app.config["FILE_URL_EXPIRATION"])
def process_html(html: str) -> str:
    # parse the html
    soup = bs4.BeautifulSoup(html, "html.parser")

    # get all anchor tags
    a_tags = soup.find_all("a")

    # make list of all filekey, url pairs
    filekey_url_pairs = [
        (app.libraries.url.url_filename(a_tag["href"], True), a_tag["href"])
        for a_tag in a_tags
    ]

    # bulk insert
    database_backend.bulk_add_file_url_keys(filekey_url_pairs)

    # rewrite the anchor tags
    for filekey_url_pair, a_tag in zip(filekey_url_pairs, a_tags):
        a_tag["href"] = unquote(
            flask.url_for(
                "files.proxy",
                filekey=filekey_url_pair[0],
                _external=True,
            )
        )

    return soup.prettify()


@simple_bp.route("/<string:projectname>/")
def project(projectname: str) -> flask.Response:
    # get the cached data from the upstream
    url_cache = proxy.get(
        f"{flask_app.config['UPSTREAM_URL']}/{url_prefix}/{projectname}"
    )

    # if the response is bad, return as-is
    if url_cache["status_code"] != http.HTTPStatus.OK:
        return flask.Response(
            url_cache["content"],
            url_cache["status_code"],
            url_cache["headers"],
        )

    # craft response
    return flask.Response(
        process_html(url_cache["content"]),
        url_cache["status_code"],
        url_cache["headers"],
    )
