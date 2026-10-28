import json
from urllib.parse import parse_qs

import pytest
from mocks.http_server import FakeServer, Response

from tide.infrastructure.http.session_client import SessionClient
from tide.infrastructure.qbittorrent.qbittorrent_service import QbittorrentService


# qBittorrent at the FakeServer, signed in with this login.
def qbittorrent(server: FakeServer, username: str, password: str) -> QbittorrentService:
    return QbittorrentService(SessionClient(server.url, 30), username=username, password=password)


# qBittorrent's answers: this answer to the login, with the session cookie, and its preferences saved.
def answer(server: FakeServer, login: str) -> None:
    server.routes[("POST", "/auth/login")] = Response(body=login, headers={"Set-Cookie": "SID=session; path=/"})
    server.routes[("POST", "/app/setPreferences")] = Response()


# qBittorrent 5.2's answer to a wrong login.
def refuse(server: FakeServer) -> None:
    server.routes[("POST", "/auth/login")] = Response(status=401, body="Unauthorized")
    server.routes[("POST", "/app/setPreferences")] = Response()


class TestGivenSkipSlowTorrents:
    def test_should_sign_in_with_the_login(self, fake_server):
        answer(fake_server, "")

        qbittorrent(fake_server, "admin", "qbit-password").skip_slow_torrents()

        assert parse_qs(fake_server.requests_to("/auth/login")[0].body) == {
            "username": ["admin"],
            "password": ["qbit-password"],
        }

    def test_should_leave_the_slow_torrents_out_of_the_limit(self, fake_server):
        answer(fake_server, "")

        qbittorrent(fake_server, "admin", "qbit-password").skip_slow_torrents()

        assert json.loads(parse_qs(fake_server.requests_to("/app/setPreferences")[0].body)["json"][0]) == {
            "dont_count_slow_torrents": True
        }

    def test_should_save_the_preferences_in_the_session_of_the_login(self, fake_server):
        answer(fake_server, "")

        qbittorrent(fake_server, "admin", "qbit-password").skip_slow_torrents()

        assert fake_server.requests_to("/app/setPreferences")[0].headers["Cookie"] == "SID=session"

    def test_should_save_the_preferences_when_an_older_qbittorrent_answers_ok(self, fake_server):
        answer(fake_server, "Ok.")

        qbittorrent(fake_server, "admin", "qbit-password").skip_slow_torrents()

        assert len(fake_server.requests_to("/app/setPreferences")) == 1

    def test_should_fail_with_what_qbittorrent_answered_to_a_wrong_login(self, fake_server):
        refuse(fake_server)

        with pytest.raises(OSError) as error:
            qbittorrent(fake_server, "admin", "wrong").skip_slow_torrents()

        assert str(error.value) == "POST /auth/login: HTTP 401 Unauthorized"

    def test_should_fail_with_what_an_older_qbittorrent_answered_to_a_wrong_login(self, fake_server):
        answer(fake_server, "Fails.")

        with pytest.raises(OSError) as error:
            qbittorrent(fake_server, "admin", "wrong").skip_slow_torrents()

        assert str(error.value) == "POST /auth/login: Fails."

    def test_should_not_save_the_preferences_after_a_wrong_login(self, fake_server):
        refuse(fake_server)

        with pytest.raises(OSError):
            qbittorrent(fake_server, "admin", "wrong").skip_slow_torrents()

        assert fake_server.requests_to("/app/setPreferences") == []

    def test_should_not_save_the_preferences_after_a_wrong_login_to_an_older_qbittorrent(self, fake_server):
        answer(fake_server, "Fails.")

        with pytest.raises(OSError):
            qbittorrent(fake_server, "admin", "wrong").skip_slow_torrents()

        assert fake_server.requests_to("/app/setPreferences") == []
