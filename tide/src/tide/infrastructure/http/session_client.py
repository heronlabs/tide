from collections.abc import Mapping
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, build_opener


# Form posts to the API of a service that signs in with a login instead of an API key, as qBittorrent does: the
# session cookie it sets on the login is kept and sent on the next calls. An HTTP error carries the body of the answer.
class SessionClient:
    def __init__(self, url: str, timeout: float) -> None:
        self._url = url
        self._timeout = timeout
        self._opener = build_opener(HTTPCookieProcessor())

    # Post a form and answer the body as text, since qBittorrent answers in plain text. With a body, urllib posts it as
    # application/x-www-form-urlencoded by itself.
    def post_form(self, path: str, fields: Mapping[str, str]) -> str:
        try:
            with self._opener.open(f"{self._url}{path}", urlencode(fields).encode(), self._timeout) as response:
                return response.read().decode()
        except HTTPError as error:
            raise OSError(f"POST {path}: HTTP {error.code} {error.read().decode()}") from error
