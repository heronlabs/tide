import json

import pytest
from mocks.http_server import FakeServer, Response

from tide.infrastructure.http.api_client import ApiClient
from tide.infrastructure.jellyfin.jellyfin_service import JellyfinService


# Jellyfin at the FakeServer, with the values main gives it.
def jellyfin(server: FakeServer) -> JellyfinService:
    return JellyfinService(
        ApiClient(server.url, lambda: "jellyfin-key", 30, id_in_body=False, media_browser=True),
        lambda app: f"{app}-key",
    )


# Jellyfin's answers to the repository step, with these repositories.
def repositories(server: FakeServer, items: str) -> None:
    server.routes[("GET", "/Repositories")] = Response(body=items)
    server.routes[("POST", "/Repositories")] = Response(status=204)


# Jellyfin's answers to the JellyBridge step, with these plugins installed and JellyBridge's settings as it ships.
def plugins(server: FakeServer, installed: str) -> None:
    server.routes[("GET", "/Plugins")] = Response(body=installed)
    server.routes[("GET", "/Plugins/f69e946a4b3c4e9a8f0a8d7c1b2a3e4f/Configuration")] = Response(
        body=json.dumps(
            {
                "JellyseerrUrl": "http://localhost:5055",
                "ApiKey": "",
                "LibraryDirectory": "/data/JellyBridge",
                "IsEnabled": False,
                "NetworkMap": [{"Country": "BR", "Name": "TV Cultura", "Id": 8}],
            }
        )
    )
    server.routes[("POST", "/Plugins/f69e946a4b3c4e9a8f0a8d7c1b2a3e4f/Configuration")] = Response(status=204)


# Jellyfin's answers to the Discover step, with these libraries.
def libraries(server: FakeServer, folders: str) -> None:
    server.routes[("GET", "/Library/VirtualFolders")] = Response(body=folders)
    server.routes[("POST", "/Library/VirtualFolders")] = Response(status=204)


class TestGivenAddRepository:
    def test_should_add_jelly_bridge_to_the_repositories(self, fake_server):
        repositories(
            fake_server,
            '[{"Name": "Jellyfin Stable", "Url": "https://repo.jellyfin.org/files/plugin/manifest.json", '
            '"Enabled": true}]',
        )

        jellyfin(fake_server).add_repository()

        assert json.loads(fake_server.requests[-1].body) == [
            {"Name": "Jellyfin Stable", "Url": "https://repo.jellyfin.org/files/plugin/manifest.json", "Enabled": True},
            {
                "Name": "Jelly Bridge",
                "Url": "https://raw.githubusercontent.com/kinggeorges12/JellyBridge/refs/heads/main/manifest.json",
                "Enabled": True,
            },
        ]

    def test_should_replace_the_jelly_bridge_it_has(self, fake_server):
        repositories(
            fake_server,
            '[{"Name": "Jelly Bridge", "Url": "https://example.com/manifest.json", "Enabled": false}, '
            '{"Name": "Jellyfin Stable", "Url": "https://repo.jellyfin.org/files/plugin/manifest.json", '
            '"Enabled": true}]',
        )

        jellyfin(fake_server).add_repository()

        assert json.loads(fake_server.requests[-1].body) == [
            {"Name": "Jellyfin Stable", "Url": "https://repo.jellyfin.org/files/plugin/manifest.json", "Enabled": True},
            {
                "Name": "Jelly Bridge",
                "Url": "https://raw.githubusercontent.com/kinggeorges12/JellyBridge/refs/heads/main/manifest.json",
                "Enabled": True,
            },
        ]


class TestGivenBridgeSeerr:
    def test_should_point_jellybridge_at_seerr_keeping_its_other_settings(self, fake_server):
        plugins(
            fake_server,
            '[{"Name": "Webhook", "Id": "71552a5a5c5c4350a2aeebe451a30173"}, '
            '{"Name": "JellyBridge", "Id": "f69e946a4b3c4e9a8f0a8d7c1b2a3e4f"}]',
        )

        jellyfin(fake_server).bridge_seerr()

        assert json.loads(fake_server.requests[-1].body) == {
            "JellyseerrUrl": "http://seerr:5055",
            "ApiKey": "seerr-key",
            "LibraryDirectory": "/media/Discover",
            "IsEnabled": True,
            "UserPermissionRequest4k": False,
            "EnableStartupSync": True,
            "NetworkMap": [{"Country": "BR", "Name": "TV Cultura", "Id": 8}],
        }

    def test_should_fail_when_jellybridge_is_not_installed(self, fake_server):
        plugins(fake_server, '[{"Name": "Webhook", "Id": "71552a5a5c5c4350a2aeebe451a30173"}]')

        with pytest.raises(OSError) as error:
            jellyfin(fake_server).bridge_seerr()

        assert str(error.value) == "no Name JellyBridge"


class TestGivenAddDiscover:
    def test_should_add_the_library_discover_of_movies_and_shows(self, fake_server):
        libraries(fake_server, '[{"Name": "Filmes", "CollectionType": "movies", "Locations": ["/media/movies"]}]')

        jellyfin(fake_server).add_discover()

        assert fake_server.requests[-1].query == (
            "name=Discover&collectionType=mixed&paths=%2Fmedia%2FDiscover&refreshLibrary=true"
        )

    def test_should_add_the_library_without_options(self, fake_server):
        libraries(fake_server, "[]")

        jellyfin(fake_server).add_discover()

        assert json.loads(fake_server.requests[-1].body) == {}

    def test_should_not_add_discover_again(self, fake_server):
        libraries(fake_server, '[{"Name": "Discover", "CollectionType": null, "Locations": ["/media/Discover"]}]')

        jellyfin(fake_server).add_discover()

        assert [request.method for request in fake_server.requests_to("/Library/VirtualFolders")] == ["GET"]
