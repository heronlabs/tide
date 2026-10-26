import json
import subprocess
import sys
from pathlib import Path

from mocks.http_server import FakeServer, Response


# Runs `tide wire` installed next to the Python of the tests with only the given variables: every service URL points
# at a FakeServer and every key is given, so it never reaches the real services nor runs docker.
def tide_wire(environment: dict[str, str]) -> subprocess.CompletedProcess[str]:
    command = Path(sys.executable).with_name("tide")
    return subprocess.run([command, "wire"], env=environment, capture_output=True, text=True, timeout=60, check=False)


# The variables of a wire against these six URLs.
def variables(radarr: str, sonarr: str, prowlarr: str, seerr: str, bazarr: str, jellyfin: str) -> dict[str, str]:
    return {
        "TIDE_QBIT_PASSWORD": "qbit-password",
        "TIDE_JELLYFIN_API_KEY": "jellyfin-key",
        "TIDE_LAN_HOST": "192.168.1.10",
        "TIDE_RADARR_URL": radarr,
        "TIDE_SONARR_URL": sonarr,
        "TIDE_PROWLARR_URL": prowlarr,
        "TIDE_SEERR_URL": seerr,
        "TIDE_BAZARR_URL": bazarr,
        "TIDE_JELLYFIN_URL": jellyfin,
        "TIDE_RADARR_API_KEY": "radarr-key",
        "TIDE_SONARR_API_KEY": "sonarr-key",
        "TIDE_PROWLARR_API_KEY": "prowlarr-key",
        "TIDE_SEERR_API_KEY": "seerr-key",
        "TIDE_BAZARR_API_KEY": "bazarr-key",
    }


# Answers like a fresh Radarr or Sonarr, whose qBittorrent category field is category_field and whose id of
# Portuguese (Brazil) is portuguese_id.
def answer_like_an_arr(server: FakeServer, category_field: str, portuguese_id: int) -> None:
    server.routes.update(
        {
            ("GET", "/api/v3/rootfolder"): Response(body="[]"),
            ("POST", "/api/v3/rootfolder"): Response(body="{}"),
            ("GET", "/api/v3/config/naming"): Response(body='{"id": 1, "renameMovies": false}'),
            ("PUT", "/api/v3/config/naming/1"): Response(body="{}"),
            ("GET", "/api/v3/language"): Response(
                body=json.dumps([{"id": 1, "name": "English"}, {"id": portuguese_id, "name": "Portuguese (Brazil)"}])
            ),
            ("GET", "/api/v3/customformat"): Response(body="[]"),
            ("POST", "/api/v3/customformat"): Response(body='{"id": 1, "name": "Portuguese (Brazil)"}'),
            ("GET", "/api/v3/qualityprofile"): Response(
                body='[{"id": 4, "name": "HD-1080p", "formatItems": [{"format": 1, "score": 0}]}]'
            ),
            ("PUT", "/api/v3/qualityprofile/4"): Response(body="{}"),
            ("GET", "/api/v3/downloadclient/schema"): Response(
                body=json.dumps(
                    [{"implementation": "QBittorrent", "name": "", "fields": [{"name": category_field, "value": None}]}]
                )
            ),
            ("GET", "/api/v3/downloadclient"): Response(body="[]"),
            ("POST", "/api/v3/downloadclient"): Response(body="{}"),
            ("GET", "/api/v3/notification/schema"): Response(
                body='[{"implementation": "MediaBrowser", "name": "", "fields": []}]'
            ),
            ("GET", "/api/v3/notification"): Response(body="[]"),
            ("POST", "/api/v3/notification"): Response(body="{}"),
            ("GET", "/api/v3/config/mediamanagement"): Response(body='{"id": 1, "importExtraFiles": false}'),
            ("PUT", "/api/v3/config/mediamanagement/1"): Response(body="{}"),
        }
    )


# Answers like a fresh Prowlarr.
def answer_like_prowlarr(server: FakeServer) -> None:
    server.routes[("GET", "/api/v1/applications/schema")] = Response(
        body='[{"implementation": "Radarr", "fields": []}, {"implementation": "Sonarr", "fields": []}]'
    )
    server.routes[("GET", "/api/v1/applications")] = Response(body="[]")
    server.routes[("POST", "/api/v1/applications")] = Response(body="{}")


# Answers like a Seerr without servers, signed in to a Jellyfin with the library Filmes.
def answer_like_seerr(server: FakeServer) -> None:
    test = Response(body='{"profiles": [{"id": 4, "name": "HD-1080p"}]}')
    server.routes[("POST", "/api/v1/settings/radarr/test")] = test
    server.routes[("POST", "/api/v1/settings/sonarr/test")] = test
    server.routes[("GET", "/api/v1/settings/radarr")] = Response(body="[]")
    server.routes[("GET", "/api/v1/settings/sonarr")] = Response(body="[]")
    server.routes[("POST", "/api/v1/settings/radarr")] = Response(body="{}")
    server.routes[("POST", "/api/v1/settings/sonarr")] = Response(body="{}")
    server.routes[("POST", "/api/v1/settings/jellyfin/library/sync")] = Response(
        body='[{"id": "a1", "name": "Filmes", "enabled": false, "type": "movie"}]'
    )
    server.routes[("PUT", "/api/v1/settings/jellyfin/library/a1")] = Response(body="{}")


# Answers like a fresh Bazarr.
def answer_like_bazarr(server: FakeServer) -> None:
    server.routes[("GET", "/api/system/languages/profiles")] = Response(body="[]")
    server.routes[("GET", "/api/system/languages")] = Response(body='[{"code2": "pb", "enabled": false}]')
    server.routes[("GET", "/api/system/settings")] = Response(body='{"general": {"enabled_providers": []}}')
    server.routes[("POST", "/api/system/settings")] = Response(status=204)


# Answers like a fresh Jellyfin with JellyBridge installed.
def answer_like_jellyfin(server: FakeServer) -> None:
    server.routes[("GET", "/Repositories")] = Response(body="[]")
    server.routes[("POST", "/Repositories")] = Response(status=204)
    server.routes[("GET", "/Plugins")] = Response(body='[{"Name": "JellyBridge", "Id": "f69e946a"}]')
    server.routes[("GET", "/Plugins/f69e946a/Configuration")] = Response(body='{"IsEnabled": false}')
    server.routes[("POST", "/Plugins/f69e946a/Configuration")] = Response(status=204)
    server.routes[("GET", "/Library/VirtualFolders")] = Response(body="[]")
    server.routes[("POST", "/Library/VirtualFolders")] = Response(status=204)


class TestGivenExecute:
    def test_should_wire_every_service(self, fake_servers):
        radarr, sonarr, prowlarr, seerr = fake_servers(), fake_servers(), fake_servers(), fake_servers()
        bazarr, jellyfin = fake_servers(), fake_servers()
        answer_like_an_arr(radarr, "movieCategory", 30)
        answer_like_an_arr(sonarr, "tvCategory", 33)
        answer_like_prowlarr(prowlarr)
        answer_like_seerr(seerr)
        answer_like_bazarr(bazarr)
        answer_like_jellyfin(jellyfin)

        result = tide_wire(variables(radarr.url, sonarr.url, prowlarr.url, seerr.url, bazarr.url, jellyfin.url))

        assert result.returncode == 0 and result.stdout.endswith("wire: 24 done, 0 failed\n")

    def test_should_give_qbittorrent_the_category_of_sonarr(self, fake_servers):
        radarr, sonarr, prowlarr, seerr = fake_servers(), fake_servers(), fake_servers(), fake_servers()
        bazarr, jellyfin = fake_servers(), fake_servers()
        answer_like_an_arr(radarr, "movieCategory", 30)
        answer_like_an_arr(sonarr, "tvCategory", 33)
        answer_like_prowlarr(prowlarr)
        answer_like_seerr(seerr)
        answer_like_bazarr(bazarr)
        answer_like_jellyfin(jellyfin)

        tide_wire(variables(radarr.url, sonarr.url, prowlarr.url, seerr.url, bazarr.url, jellyfin.url))

        assert json.loads(sonarr.requests_to("/api/v3/downloadclient")[-1].body)["fields"] == [
            {"name": "tvCategory", "value": "sonarr"}
        ]

    def test_should_give_sonarr_the_custom_format_of_its_id_of_portuguese(self, fake_servers):
        radarr, sonarr, prowlarr, seerr = fake_servers(), fake_servers(), fake_servers(), fake_servers()
        bazarr, jellyfin = fake_servers(), fake_servers()
        answer_like_an_arr(radarr, "movieCategory", 30)
        answer_like_an_arr(sonarr, "tvCategory", 33)
        answer_like_prowlarr(prowlarr)
        answer_like_seerr(seerr)
        answer_like_bazarr(bazarr)
        answer_like_jellyfin(jellyfin)

        tide_wire(variables(radarr.url, sonarr.url, prowlarr.url, seerr.url, bazarr.url, jellyfin.url))

        assert json.loads(sonarr.requests_to("/api/v3/customformat")[-1].body)["specifications"][0]["fields"] == [
            {"name": "value", "value": 33},
            {"name": "exceptLanguage", "value": False},
        ]

    def test_should_replace_the_server_seerr_has_without_sending_its_id(self, fake_servers):
        radarr, sonarr, prowlarr, seerr = fake_servers(), fake_servers(), fake_servers(), fake_servers()
        bazarr, jellyfin = fake_servers(), fake_servers()
        answer_like_an_arr(radarr, "movieCategory", 30)
        answer_like_an_arr(sonarr, "tvCategory", 33)
        answer_like_prowlarr(prowlarr)
        answer_like_seerr(seerr)
        answer_like_bazarr(bazarr)
        answer_like_jellyfin(jellyfin)
        seerr.routes[("GET", "/api/v1/settings/radarr")] = Response(body='[{"id": 0, "name": "Radarr"}]')
        seerr.routes[("PUT", "/api/v1/settings/radarr/0")] = Response(body="{}")

        tide_wire(variables(radarr.url, sonarr.url, prowlarr.url, seerr.url, bazarr.url, jellyfin.url))

        assert "id" not in json.loads(seerr.requests_to("/api/v1/settings/radarr/0")[0].body)

    def test_should_have_bazarr_follow_sonarr_with_its_key(self, fake_servers):
        radarr, sonarr, prowlarr, seerr = fake_servers(), fake_servers(), fake_servers(), fake_servers()
        bazarr, jellyfin = fake_servers(), fake_servers()
        answer_like_an_arr(radarr, "movieCategory", 30)
        answer_like_an_arr(sonarr, "tvCategory", 33)
        answer_like_prowlarr(prowlarr)
        answer_like_seerr(seerr)
        answer_like_bazarr(bazarr)
        answer_like_jellyfin(jellyfin)

        tide_wire(variables(radarr.url, sonarr.url, prowlarr.url, seerr.url, bazarr.url, jellyfin.url))

        assert "settings-sonarr-apikey=sonarr-key" in bazarr.requests_to("/api/system/settings")[-1].body

    def test_should_have_bazarr_enable_opensubtitles_with_its_login(self, fake_servers):
        radarr, sonarr, prowlarr, seerr = fake_servers(), fake_servers(), fake_servers(), fake_servers()
        bazarr, jellyfin = fake_servers(), fake_servers()
        answer_like_an_arr(radarr, "movieCategory", 30)
        answer_like_an_arr(sonarr, "tvCategory", 33)
        answer_like_prowlarr(prowlarr)
        answer_like_seerr(seerr)
        answer_like_bazarr(bazarr)
        answer_like_jellyfin(jellyfin)
        environment = variables(radarr.url, sonarr.url, prowlarr.url, seerr.url, bazarr.url, jellyfin.url)
        environment["TIDE_OPENSUBTITLES_USERNAME"] = "lucas"
        environment["TIDE_OPENSUBTITLES_PASSWORD"] = "opensubtitles-password"

        tide_wire(environment)

        assert [
            request.body
            for request in bazarr.requests_to("/api/system/settings")
            if "enabled_providers" in request.body
        ] == [
            "settings-general-enabled_providers=opensubtitlescom&settings-opensubtitlescom-username=lucas"
            "&settings-opensubtitlescom-password=opensubtitles-password"
        ]

    def test_should_have_bazarr_enable_no_provider_without_the_opensubtitles_login(self, fake_servers):
        radarr, sonarr, prowlarr, seerr = fake_servers(), fake_servers(), fake_servers(), fake_servers()
        bazarr, jellyfin = fake_servers(), fake_servers()
        answer_like_an_arr(radarr, "movieCategory", 30)
        answer_like_an_arr(sonarr, "tvCategory", 33)
        answer_like_prowlarr(prowlarr)
        answer_like_seerr(seerr)
        answer_like_bazarr(bazarr)
        answer_like_jellyfin(jellyfin)

        tide_wire(variables(radarr.url, sonarr.url, prowlarr.url, seerr.url, bazarr.url, jellyfin.url))

        assert [
            request.body
            for request in bazarr.requests_to("/api/system/settings")
            if "enabled_providers" in request.body
        ] == []

    def test_should_send_jellyfin_its_key_as_a_media_browser_token(self, fake_servers):
        radarr, sonarr, prowlarr, seerr = fake_servers(), fake_servers(), fake_servers(), fake_servers()
        bazarr, jellyfin = fake_servers(), fake_servers()
        answer_like_an_arr(radarr, "movieCategory", 30)
        answer_like_an_arr(sonarr, "tvCategory", 33)
        answer_like_prowlarr(prowlarr)
        answer_like_seerr(seerr)
        answer_like_bazarr(bazarr)
        answer_like_jellyfin(jellyfin)

        tide_wire(variables(radarr.url, sonarr.url, prowlarr.url, seerr.url, bazarr.url, jellyfin.url))

        assert jellyfin.requests[0].headers["Authorization"] == 'MediaBrowser Token="jellyfin-key"'

    def test_should_wire_the_others_when_radarr_is_down(self, fake_servers):
        down = fake_servers()
        down.stop()
        sonarr, prowlarr, seerr, bazarr = fake_servers(), fake_servers(), fake_servers(), fake_servers()
        jellyfin = fake_servers()
        answer_like_an_arr(sonarr, "tvCategory", 33)
        answer_like_prowlarr(prowlarr)
        answer_like_seerr(seerr)
        answer_like_bazarr(bazarr)
        answer_like_jellyfin(jellyfin)

        result = tide_wire(variables(down.url, sonarr.url, prowlarr.url, seerr.url, bazarr.url, jellyfin.url))

        assert result.returncode == 1 and result.stdout.endswith("wire: 18 done, 6 failed\n")

    def test_should_exit_with_code_two_without_the_qbittorrent_password(self, fake_servers):
        server = fake_servers()
        environment = variables(server.url, server.url, server.url, server.url, server.url, server.url)
        del environment["TIDE_QBIT_PASSWORD"]

        result = tide_wire(environment)

        assert result.returncode == 2 and "TIDE_QBIT_PASSWORD is not set" in result.stderr
