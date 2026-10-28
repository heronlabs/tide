import pytest
from mocks.http_server import Response

from tide.infrastructure.http.session_client import SessionClient


class TestGivenPostForm:
    def test_should_answer_the_body_as_text(self, fake_server):
        fake_server.routes[("POST", "/api/v2/auth/login")] = Response(body="Ok.")

        answer = SessionClient(f"{fake_server.url}/api/v2", 30).post_form("/auth/login", {"username": "admin"})

        assert answer == "Ok."

    def test_should_answer_an_empty_body_as_empty_text(self, fake_server):
        fake_server.routes[("POST", "/auth/login")] = Response(status=204)

        answer = SessionClient(fake_server.url, 30).post_form("/auth/login", {"username": "admin"})

        assert answer == ""

    def test_should_post_the_fields_as_a_form(self, fake_server):
        fake_server.routes[("POST", "/auth/login")] = Response(body="Ok.")

        SessionClient(fake_server.url, 30).post_form("/auth/login", {"username": "admin", "password": "a&b"})

        assert (fake_server.requests[0].headers["Content-Type"], fake_server.requests[0].body) == (
            "application/x-www-form-urlencoded",
            "username=admin&password=a%26b",
        )

    def test_should_send_the_cookie_of_the_session_on_the_next_calls(self, fake_server):
        fake_server.routes[("POST", "/auth/login")] = Response(body="Ok.", headers={"Set-Cookie": "SID=abc; path=/"})
        fake_server.routes[("POST", "/app/setPreferences")] = Response()
        client = SessionClient(fake_server.url, 30)
        client.post_form("/auth/login", {"username": "admin"})

        client.post_form("/app/setPreferences", {"json": "{}"})

        assert fake_server.requests_to("/app/setPreferences")[0].headers["Cookie"] == "SID=abc"

    def test_should_give_up_when_the_service_does_not_answer_in_time(self, fake_server):
        fake_server.routes[("POST", "/auth/login")] = Response(body="Ok.", delay=0.5)

        with pytest.raises(TimeoutError):
            SessionClient(fake_server.url, 0.05).post_form("/auth/login", {"username": "admin"})

    def test_should_fail_with_what_the_service_answered(self, fake_server):
        fake_server.routes[("POST", "/auth/login")] = Response(status=403, body="Forbidden")

        with pytest.raises(OSError) as error:
            SessionClient(fake_server.url, 30).post_form("/auth/login", {"username": "admin"})

        assert str(error.value) == "POST /auth/login: HTTP 403 Forbidden"
