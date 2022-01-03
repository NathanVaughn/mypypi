import http

import app.lib.proxy
import app.lib.url
import bs4
import flask

url_prefix = "simple"
simple_bp = flask.Blueprint("simple", __name__, url_prefix=f"/{url_prefix}")


def process_html(html: bytes):
    """
    Rewrite all file URLs in a simple page with our file proxy.
    """
    soup = bs4.BeautifulSoup(html, "html.parser")
    for a_tag in soup.find_all("a"):
        a_tag["href"] = app.lib.url.proxy_url(a_tag["href"])

    return soup.prettify()


@simple_bp.route("/<string:projectname>/")
def project(projectname: str):
    # make request to upstream
    status_code, content, headers = app.lib.proxy.reverse_proxy(
        f'{flask.current_app.config.UPSTREAM_URL}/{url_prefix}/{projectname}'
    )

    if status_code != http.HTTPStatus.OK:
        return flask.Response(content, status_code, headers)

    # process html
    new_html = process_html(content)

    # craft response
    return flask.Response(new_html, status_code, headers)
