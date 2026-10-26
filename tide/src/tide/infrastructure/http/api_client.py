import json
from collections.abc import Callable, Mapping
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

JSON = "application/json"
FORM = "application/x-www-form-urlencoded"


# JSON calls to the API of one service, authenticated by its API key, which is asked for on each call.
# An HTTP error carries the body of the answer, where the services say what they rejected, and an empty answer,
# such as Jellyfin's 204 No Content, is None.
# id_in_body: the *arr APIs want the id of an item they replace in its body too; Seerr rejects it as read-only.
# media_browser: Jellyfin takes the key only as the Authorization of its scheme MediaBrowser, not as X-Api-Key.
class ApiClient:
    def __init__(self, url: str, key: Callable[[], str], timeout: float, id_in_body: bool, media_browser: bool) -> None:
        self._url = url
        self._key = key
        self._timeout = timeout
        self._id_in_body = id_in_body
        self._media_browser = media_browser

    def get(self, path: str) -> Any:
        return _parse(self._send("GET", path, None, JSON))

    def post(self, path: str, body: object) -> Any:
        return _parse(self._send("POST", path, json.dumps(body).encode(), JSON))

    def put(self, path: str, body: object) -> Any:
        return _parse(self._send("PUT", path, json.dumps(body).encode(), JSON))

    # Post a form, as Bazarr takes its settings, a field with a list once per value, and ignore the empty answer.
    def post_form(self, path: str, fields: Mapping[str, str | list[str]]) -> None:
        self._send("POST", path, urlencode(fields, doseq=True).encode(), FORM)

    # Replace the item under path named like the body, or add it, and answer the item as saved.
    def upsert(self, path: str, body: dict[str, Any]) -> Any:
        ids = [item["id"] for item in self.get(path) if item["name"] == body["name"]]
        if not ids:
            return self.post(path, body)
        return self.put(f"{path}/{ids[0]}", {**body, "id": ids[0]} if self._id_in_body else body)

    def _send(self, method: str, path: str, data: bytes | None, content_type: str) -> bytes:
        request = Request(f"{self._url}{path}", data=data, method=method, headers=self._headers(content_type))
        try:
            with urlopen(request, timeout=self._timeout) as response:
                return response.read()
        except HTTPError as error:
            raise OSError(f"{method} {path}: HTTP {error.code} {error.read().decode()}") from error

    def _headers(self, content_type: str) -> dict[str, str]:
        # urllib normalizes the case of header names, so a mutant that changes the case of one is equivalent.
        if self._media_browser:
            token = f'MediaBrowser Token="{self._key()}"'
            return {"Authorization": token, "Content-Type": content_type}  # pragma: no mutate
        return {"X-Api-Key": self._key(), "Content-Type": content_type}  # pragma: no mutate


def _parse(answer: bytes) -> Any:
    return json.loads(answer) if answer else None
