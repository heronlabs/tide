import json

from mocks.http_server import FakeServer, Response

from tide.infrastructure.http.api_client import ApiClient
from tide.infrastructure.prowlarr.prowlarr_service import ProwlarrService


# The application schemas Prowlarr answers, for Radarr and Sonarr.
def schemas(server: FakeServer) -> None:
    server.routes[("GET", "/applications/schema")] = Response(
        body=json.dumps(
            [
                {
                    "implementation": "Radarr",
                    "name": "",
                    "syncLevel": "addOnly",
                    "fields": [
                        {"name": "prowlarrUrl", "value": "http://localhost:9696"},
                        {"name": "baseUrl", "value": "http://localhost:7878"},
                        {"name": "apiKey", "value": None},
                        {"name": "syncCategories", "value": [2000]},
                    ],
                },
                {
                    "implementation": "Sonarr",
                    "name": "",
                    "syncLevel": "addOnly",
                    "fields": [
                        {"name": "prowlarrUrl", "value": "http://localhost:9696"},
                        {"name": "baseUrl", "value": "http://localhost:8989"},
                        {"name": "apiKey", "value": None},
                        {"name": "syncCategories", "value": [5000]},
                    ],
                },
            ]
        )
    )


class TestGivenSync:
    def test_should_add_radarr_with_full_sync(self, fake_server):
        schemas(fake_server)
        fake_server.routes[("GET", "/applications")] = Response(body="[]")
        fake_server.routes[("POST", "/applications")] = Response(body="{}")

        ProwlarrService(
            ApiClient(fake_server.url, lambda: "prowlarr-key", 30, id_in_body=True, media_browser=False),
            lambda app: f"{app}-key",
        ).sync("radarr")

        assert json.loads(fake_server.requests[-1].body) == {
            "implementation": "Radarr",
            "name": "Radarr",
            "syncLevel": "fullSync",
            "fields": [
                {"name": "prowlarrUrl", "value": "http://prowlarr:9696"},
                {"name": "baseUrl", "value": "http://radarr:7878"},
                {"name": "apiKey", "value": "radarr-key"},
                {"name": "syncCategories", "value": [2000]},
            ],
        }

    def test_should_add_sonarr_at_its_address(self, fake_server):
        schemas(fake_server)
        fake_server.routes[("GET", "/applications")] = Response(body="[]")
        fake_server.routes[("POST", "/applications")] = Response(body="{}")

        ProwlarrService(
            ApiClient(fake_server.url, lambda: "prowlarr-key", 30, id_in_body=True, media_browser=False),
            lambda app: f"{app}-key",
        ).sync("sonarr")

        assert json.loads(fake_server.requests[-1].body)["fields"][1] == {
            "name": "baseUrl",
            "value": "http://sonarr:8989",
        }
