import http

import bs4
import flask

import app.libraries.proxy
from app.main import cache

url_prefix = "simple"
simple_bp = flask.Blueprint("simple", __name__, url_prefix=f"/{url_prefix}")


def process_html(html: bytes) -> str:
    """
    Rewrite all file URLs in a simple page with our file proxy.
    """
    soup = bs4.BeautifulSoup(html, "html.parser")

    a_tags = soup.find_all("a")

    urls = [a["href"] for a in a_tags]
    proxy_urls = app.libraries.proxy.proxy_urls(urls)

    for a_tag, proxy_url in zip(a_tags, proxy_urls):
        a_tag["href"] = proxy_url

    return soup.prettify()


@simple_bp.route("/<string:projectname>/")
@cache.cached()
def project(projectname: str) -> flask.Response:
    # make request to upstream
    status_code, content, headers = app.libraries.proxy.reverse_proxy(
        f"{flask.current_app.config.UPSTREAM_URL}/{url_prefix}/{projectname}"
    )

    if status_code != http.HTTPStatus.OK:
        return flask.Response(content, status_code, headers)

    # process html
    new_html = process_html(content)

    # craft response
    return flask.Response(new_html, status_code, headers)
