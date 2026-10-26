import json

import pytest
from mocks.http_server import Response

from tide.infrastructure.http.api_client import ApiClient


class TestGivenGet:
    def test_should_answer_the_parsed_body(self, fake_server):
        fake_server.routes[("GET", "/api/v3/rootfolder")] = Response(body='[{"path": "/data/movies"}]')

        folders = ApiClient(
            f"{fake_server.url}/api/v3", lambda: "secret", 30, id_in_body=True, media_browser=False
        ).get("/rootfolder")

        assert folders == [{"path": "/data/movies"}]

    def test_should_send_the_api_key(self, fake_server):
        fake_server.routes[("GET", "/rootfolder")] = Response(body="[]")

        ApiClient(fake_server.url, lambda: "secret", 30, id_in_body=True, media_browser=False).get("/rootfolder")

        assert fake_server.requests[0].headers["X-Api-Key"] == "secret"

    def test_should_send_the_api_key_as_a_media_browser_token_to_jellyfin(self, fake_server):
        fake_server.routes[("GET", "/Plugins")] = Response(body="[]")

        ApiClient(fake_server.url, lambda: "secret", 30, id_in_body=False, media_browser=True).get("/Plugins")

        assert fake_server.requests[0].headers["Authorization"] == 'MediaBrowser Token="secret"'

    def test_should_give_up_when_the_service_does_not_answer_in_time(self, fake_server):
        fake_server.routes[("GET", "/rootfolder")] = Response(body="[]", delay=0.5)

        with pytest.raises(TimeoutError):
            ApiClient(fake_server.url, lambda: "secret", 0.05, id_in_body=True, media_browser=False).get("/rootfolder")

    def test_should_fail_with_what_the_service_answered(self, fake_server):
        fake_server.routes[("GET", "/rootfolder")] = Response(status=401, body='{"message": "Unauthorized"}')

        with pytest.raises(OSError) as error:
            ApiClient(fake_server.url, lambda: "wrong", 30, id_in_body=True, media_browser=False).get("/rootfolder")

        assert str(error.value) == 'GET /rootfolder: HTTP 401 {"message": "Unauthorized"}'

    def test_should_get_without_a_body(self, fake_server):
        fake_server.routes[("GET", "/rootfolder")] = Response(body="[]")

        ApiClient(fake_server.url, lambda: "secret", 30, id_in_body=True, media_browser=False).get("/rootfolder")

        assert fake_server.requests[0].body == ""


class TestGivenPost:
    def test_should_post_the_body_as_json(self, fake_server):
        fake_server.routes[("POST", "/rootfolder")] = Response(body="{}")

        ApiClient(fake_server.url, lambda: "secret", 30, id_in_body=True, media_browser=False).post(
            "/rootfolder", {"path": "/data/movies"}
        )

        assert json.loads(fake_server.requests_to("/rootfolder")[0].body) == {"path": "/data/movies"}

    def test_should_say_the_body_is_json(self, fake_server):
        fake_server.routes[("POST", "/rootfolder")] = Response(body="{}")

        ApiClient(fake_server.url, lambda: "secret", 30, id_in_body=True, media_browser=False).post(
            "/rootfolder", {"path": "/data/movies"}
        )

        assert fake_server.requests_to("/rootfolder")[0].headers["Content-Type"] == "application/json"

    def test_should_say_the_body_is_json_to_jellyfin(self, fake_server):
        fake_server.routes[("POST", "/Repositories")] = Response(status=204)

        ApiClient(fake_server.url, lambda: "secret", 30, id_in_body=False, media_browser=True).post("/Repositories", [])

        assert fake_server.requests_to("/Repositories")[0].headers["Content-Type"] == "application/json"

    def test_should_answer_the_parsed_body(self, fake_server):
        fake_server.routes[("POST", "/rootfolder")] = Response(body='{"id": 1, "path": "/data/movies"}')

        folder = ApiClient(fake_server.url, lambda: "secret", 30, id_in_body=True, media_browser=False).post(
            "/rootfolder", {"path": "/data/movies"}
        )

        assert folder == {"id": 1, "path": "/data/movies"}

    def test_should_answer_none_when_the_service_answers_no_content(self, fake_server):
        fake_server.routes[("POST", "/Repositories")] = Response(status=204)

        answer = ApiClient(fake_server.url, lambda: "secret", 30, id_in_body=False, media_browser=True).post(
            "/Repositories", []
        )

        assert answer is None

    def test_should_fail_naming_the_post(self, fake_server):
        fake_server.routes[("POST", "/rootfolder")] = Response(status=400, body='[{"errorMessage": "Invalid path"}]')

        with pytest.raises(OSError) as error:
            ApiClient(fake_server.url, lambda: "secret", 30, id_in_body=True, media_browser=False).post(
                "/rootfolder", {"path": "data"}
            )

        assert str(error.value) == 'POST /rootfolder: HTTP 400 [{"errorMessage": "Invalid path"}]'


class TestGivenPut:
    def test_should_put_the_body_as_json(self, fake_server):
        fake_server.routes[("PUT", "/config/naming/1")] = Response(body="{}")

        ApiClient(fake_server.url, lambda: "secret", 30, id_in_body=True, media_browser=False).put(
            "/config/naming/1", {"id": 1, "renameMovies": True}
        )

        assert json.loads(fake_server.requests_to("/config/naming/1")[0].body) == {"id": 1, "renameMovies": True}


class TestGivenPostForm:
    def test_should_post_the_fields_as_a_form_repeating_a_list(self, fake_server):
        fake_server.routes[("POST", "/system/settings")] = Response(status=204)

        ApiClient(fake_server.url, lambda: "secret", 30, id_in_body=False, media_browser=False).post_form(
            "/system/settings", {"settings-radarr-ip": "radarr", "languages-enabled": ["en", "pb"]}
        )

        assert fake_server.requests_to("/system/settings")[0].body == (
            "settings-radarr-ip=radarr&languages-enabled=en&languages-enabled=pb"
        )

    def test_should_say_the_body_is_a_form(self, fake_server):
        fake_server.routes[("POST", "/system/settings")] = Response(status=204)

        ApiClient(fake_server.url, lambda: "secret", 30, id_in_body=False, media_browser=False).post_form(
            "/system/settings", {"a": "b"}
        )

        assert fake_server.requests_to("/system/settings")[0].headers["Content-Type"] == (
            "application/x-www-form-urlencoded"
        )

    def test_should_fail_naming_the_post(self, fake_server):
        fake_server.routes[("POST", "/system/settings")] = Response(status=406, body="Invalid value")

        with pytest.raises(OSError) as error:
            ApiClient(fake_server.url, lambda: "secret", 30, id_in_body=False, media_browser=False).post_form(
                "/system/settings", {}
            )

        assert str(error.value) == "POST /system/settings: HTTP 406 Invalid value"


class TestGivenUpsert:
    def test_should_post_the_item_when_none_has_its_name(self, fake_server):
        fake_server.routes[("GET", "/customformat")] = Response(body='[{"id": 1, "name": "x265"}]')
        fake_server.routes[("POST", "/customformat")] = Response(body='{"id": 2, "name": "Portuguese (Brazil)"}')

        ApiClient(fake_server.url, lambda: "secret", 30, id_in_body=True, media_browser=False).upsert(
            "/customformat", {"name": "Portuguese (Brazil)"}
        )

        assert [request.method for request in fake_server.requests_to("/customformat")] == ["GET", "POST"]

    def test_should_answer_the_item_as_saved(self, fake_server):
        fake_server.routes[("GET", "/customformat")] = Response(body="[]")
        fake_server.routes[("POST", "/customformat")] = Response(body='{"id": 2, "name": "Portuguese (Brazil)"}')

        saved = ApiClient(fake_server.url, lambda: "secret", 30, id_in_body=True, media_browser=False).upsert(
            "/customformat", {"name": "Portuguese (Brazil)"}
        )

        assert saved == {"id": 2, "name": "Portuguese (Brazil)"}

    def test_should_put_the_item_with_its_id_over_the_one_with_its_name(self, fake_server):
        fake_server.routes[("GET", "/customformat")] = Response(
            body='[{"id": 1, "name": "x265"}, {"id": 7, "name": "Portuguese (Brazil)"}]'
        )
        fake_server.routes[("PUT", "/customformat/7")] = Response(body='{"id": 7, "name": "Portuguese (Brazil)"}')

        ApiClient(fake_server.url, lambda: "secret", 30, id_in_body=True, media_browser=False).upsert(
            "/customformat", {"name": "Portuguese (Brazil)", "negate": False}
        )

        assert json.loads(fake_server.requests_to("/customformat/7")[0].body) == {
            "name": "Portuguese (Brazil)",
            "negate": False,
            "id": 7,
        }

    def test_should_put_the_item_without_its_id_when_the_service_rejects_it(self, fake_server):
        fake_server.routes[("GET", "/settings/radarr")] = Response(body='[{"id": 0, "name": "Radarr"}]')
        fake_server.routes[("PUT", "/settings/radarr/0")] = Response(body='{"id": 0, "name": "Radarr"}')

        ApiClient(fake_server.url, lambda: "secret", 30, id_in_body=False, media_browser=False).upsert(
            "/settings/radarr", {"name": "Radarr", "port": 7878}
        )

        assert json.loads(fake_server.requests_to("/settings/radarr/0")[0].body) == {"name": "Radarr", "port": 7878}
