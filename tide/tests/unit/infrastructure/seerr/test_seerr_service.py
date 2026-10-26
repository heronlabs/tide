import json

from mocks.http_server import FakeServer, Response

from tide.infrastructure.http.api_client import ApiClient
from tide.infrastructure.seerr.seerr_service import SeerrService


# Seerr at the FakeServer, with the values main gives it.
def seerr(server: FakeServer) -> SeerrService:
    return SeerrService(
        ApiClient(server.url, lambda: "seerr-key", 30, id_in_body=False, media_browser=False),
        lambda app: f"{app}-key",
        quality_profile="HD-1080p",
        lan_host="192.168.1.10",
    )


# Seerr's answers to adding one server (radarr or sonarr) the first time.
def answers(server: FakeServer, app: str) -> None:
    server.routes[("POST", f"/settings/{app}/test")] = Response(
        body='{"profiles": [{"id": 1, "name": "Any"}, {"id": 4, "name": "HD-1080p"}], "rootFolders": []}'
    )
    server.routes[("GET", f"/settings/{app}")] = Response(body="[]")
    server.routes[("POST", f"/settings/{app}")] = Response(body="{}")


# Seerr's answer to the sync of the libraries: these libraries of Jellyfin.
def libraries(server: FakeServer, synced: str) -> None:
    server.routes[("POST", "/settings/jellyfin/library/sync")] = Response(body=synced)


class TestGivenSendToRadarr:
    def test_should_test_the_connection_to_radarr(self, fake_server):
        answers(fake_server, "radarr")

        seerr(fake_server).send_to_radarr()

        assert json.loads(fake_server.requests_to("/settings/radarr/test")[0].body) == {
            "hostname": "radarr",
            "port": 7878,
            "apiKey": "radarr-key",
            "useSsl": False,
            "baseUrl": "",
        }

    def test_should_add_radarr_as_the_default_server(self, fake_server):
        answers(fake_server, "radarr")

        seerr(fake_server).send_to_radarr()

        assert json.loads(fake_server.requests[-1].body) == {
            "hostname": "radarr",
            "port": 7878,
            "apiKey": "radarr-key",
            "useSsl": False,
            "baseUrl": "",
            "name": "Radarr",
            "activeProfileId": 4,
            "activeProfileName": "HD-1080p",
            "activeDirectory": "/data/movies",
            "is4k": False,
            "isDefault": True,
            "externalUrl": "http://192.168.1.10:7878",
            "syncEnabled": True,
            "preventSearch": False,
            "tags": [],
            "tagRequests": False,
            "minimumAvailability": "released",
        }


class TestGivenSendToSonarr:
    def test_should_add_sonarr_as_the_default_server_for_shows_and_anime(self, fake_server):
        answers(fake_server, "sonarr")

        seerr(fake_server).send_to_sonarr()

        assert json.loads(fake_server.requests[-1].body) == {
            "hostname": "sonarr",
            "port": 8989,
            "apiKey": "sonarr-key",
            "useSsl": False,
            "baseUrl": "",
            "name": "Sonarr",
            "activeProfileId": 4,
            "activeProfileName": "HD-1080p",
            "activeDirectory": "/data/shows",
            "is4k": False,
            "isDefault": True,
            "externalUrl": "http://192.168.1.10:8989",
            "syncEnabled": True,
            "preventSearch": False,
            "tags": [],
            "tagRequests": False,
            "activeAnimeProfileId": 4,
            "activeAnimeProfileName": "HD-1080p",
            "activeAnimeDirectory": "/data/shows",
            "animeTags": [],
            "enableSeasonFolders": True,
            "seriesType": "standard",
            "animeSeriesType": "anime",
        }


class TestGivenSkipDiscover:
    def test_should_sync_the_libraries_of_jellyfin(self, fake_server):
        libraries(fake_server, "[]")

        seerr(fake_server).skip_discover()

        assert json.loads(fake_server.requests_to("/settings/jellyfin/library/sync")[0].body) == {}

    def test_should_enable_every_library_but_discover(self, fake_server):
        libraries(
            fake_server,
            '[{"id": "a1", "name": "Filmes", "enabled": false, "type": "movie"}, '
            '{"id": "b2", "name": "Séries", "enabled": true, "type": "show"}, '
            '{"id": "d3", "name": "Discover", "enabled": true, "type": "show"}]',
        )
        fake_server.routes[("PUT", "/settings/jellyfin/library/a1")] = Response(body="{}")
        fake_server.routes[("PUT", "/settings/jellyfin/library/b2")] = Response(body="{}")
        fake_server.routes[("PUT", "/settings/jellyfin/library/d3")] = Response(body="{}")

        seerr(fake_server).skip_discover()

        assert [(request.path, json.loads(request.body)) for request in fake_server.requests[1:]] == [
            ("/settings/jellyfin/library/a1", {"enabled": True}),
            ("/settings/jellyfin/library/b2", {"enabled": True}),
            ("/settings/jellyfin/library/d3", {"enabled": False}),
        ]
