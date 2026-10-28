import json

from tide.infrastructure.http.session_client import SessionClient


# qBittorrent: downloads what Radarr and Sonarr send it, a few torrents at a time. A torrent nobody seeds would hold
# its place in the queue forever, so the ones that barely download are left out of the limit of active downloads.
class QbittorrentService:
    def __init__(self, client: SessionClient, username: str, password: str) -> None:
        self._client = client
        self._username = username
        self._password = password

    def skip_slow_torrents(self) -> None:
        self._login()
        self._client.post_form("/app/setPreferences", {"json": json.dumps({"dont_count_slow_torrents": True})})

    # qBittorrent 5.2 answers a wrong login with HTTP 401, an error of the client, but the versions before it answer
    # 200 with "Fails." (and "Ok." to a right one, which 5.2 answers empty).
    def _login(self) -> None:
        answer = self._client.post_form("/auth/login", {"username": self._username, "password": self._password})
        if answer == "Fails.":
            raise OSError(f"POST /auth/login: {answer}")
