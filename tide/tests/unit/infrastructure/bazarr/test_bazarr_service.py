import json
from urllib.parse import parse_qs

from mocks.http_server import FakeServer, Response

from tide.infrastructure.bazarr.bazarr_service import BazarrService
from tide.infrastructure.http.api_client import ApiClient


# Bazarr at the FakeServer, with the values main gives it and the OpenSubtitles.com login, if any.
def bazarr(server: FakeServer, username: str | None = None, password: str | None = None) -> BazarrService:
    return BazarrService(
        ApiClient(server.url, lambda: "bazarr-key", 30, id_in_body=False, media_browser=False),
        lambda app: f"{app}-key",
        opensubtitles_username=username,
        opensubtitles_password=password,
    )


# Bazarr's answers to the languages step: these profiles and these languages enabled.
def languages(server: FakeServer, profiles: str, enabled: str) -> None:
    server.routes[("GET", "/system/languages/profiles")] = Response(body=profiles)
    server.routes[("GET", "/system/languages")] = Response(body=enabled)
    server.routes[("POST", "/system/settings")] = Response(status=204)


# Bazarr's answers to the providers step, with these providers enabled.
def providers(server: FakeServer, enabled: str) -> None:
    server.routes[("GET", "/system/settings")] = Response(body=f'{{"general": {{"enabled_providers": {enabled}}}}}')
    server.routes[("POST", "/system/settings")] = Response(status=204)


# The form Bazarr got on its settings, each field with its list of values.
def form(server: FakeServer) -> dict[str, list[str]]:
    return parse_qs(server.requests_to("/system/settings")[-1].body)


class TestGivenPreferPortuguese:
    def test_should_add_the_profile_as_the_default_of_movies_and_shows(self, fake_server):
        languages(fake_server, "[]", '[{"code2": "en", "enabled": false}]')

        bazarr(fake_server).prefer_portuguese()

        assert form(fake_server) == {
            "languages-enabled": ["pb"],
            "languages-profiles": [
                json.dumps(
                    [
                        {
                            "name": "Portuguese (Brazil)",
                            "cutoff": None,
                            "items": [
                                {
                                    "id": 1,
                                    "language": "pb",
                                    "audio_exclude": "False",
                                    "audio_only_include": "False",
                                    "hi": "False",
                                    "forced": "False",
                                }
                            ],
                            "mustContain": [],
                            "mustNotContain": [],
                            "originalFormat": None,
                            "tag": None,
                            "profileId": 1,
                        }
                    ]
                )
            ],
            "settings-general-movie_default_enabled": ["true"],
            "settings-general-movie_default_profile": ["1"],
            "settings-general-serie_default_enabled": ["true"],
            "settings-general-serie_default_profile": ["1"],
        }

    def test_should_keep_the_languages_already_enabled(self, fake_server):
        languages(fake_server, "[]", '[{"code2": "pb", "enabled": true}, {"code2": "en", "enabled": true}]')

        bazarr(fake_server).prefer_portuguese()

        assert form(fake_server)["languages-enabled"] == ["en", "pb"]

    def test_should_add_the_profile_after_the_other_profiles(self, fake_server):
        languages(fake_server, '[{"profileId": 2, "name": "English"}, {"profileId": 5, "name": "Spanish"}]', "[]")

        bazarr(fake_server).prefer_portuguese()

        assert [profile["profileId"] for profile in json.loads(form(fake_server)["languages-profiles"][0])] == [2, 5, 6]

    def test_should_replace_the_profile_with_its_name(self, fake_server):
        languages(
            fake_server,
            '[{"profileId": 3, "name": "Portuguese (Brazil)", "cutoff": 1}, {"profileId": 4, "name": "English"}]',
            "[]",
        )

        bazarr(fake_server).prefer_portuguese()

        assert [
            (profile["profileId"], profile["name"], profile.get("cutoff"))
            for profile in json.loads(form(fake_server)["languages-profiles"][0])
        ] == [(4, "English", None), (3, "Portuguese (Brazil)", None)]

    def test_should_make_the_replaced_profile_the_default(self, fake_server):
        languages(fake_server, '[{"profileId": 3, "name": "Portuguese (Brazil)"}]', "[]")

        bazarr(fake_server).prefer_portuguese()

        assert form(fake_server)["settings-general-movie_default_profile"] == ["3"]


class TestGivenUseProviders:
    def test_should_enable_opensubtitles_with_its_login(self, fake_server):
        providers(fake_server, "[]")

        bazarr(fake_server, "lucas", "opensubtitles-password").use_providers()

        assert form(fake_server) == {
            "settings-general-enabled_providers": ["opensubtitlescom"],
            "settings-opensubtitlescom-username": ["lucas"],
            "settings-opensubtitlescom-password": ["opensubtitles-password"],
        }

    def test_should_keep_the_providers_already_enabled(self, fake_server):
        providers(fake_server, '["podnapisi", "embeddedsubtitles"]')

        bazarr(fake_server, "lucas", "opensubtitles-password").use_providers()

        assert form(fake_server)["settings-general-enabled_providers"] == [
            "podnapisi",
            "embeddedsubtitles",
            "opensubtitlescom",
        ]

    def test_should_enable_opensubtitles_once_when_it_is_already_enabled(self, fake_server):
        providers(fake_server, '["opensubtitlescom", "podnapisi"]')

        bazarr(fake_server, "lucas", "opensubtitles-password").use_providers()

        assert form(fake_server)["settings-general-enabled_providers"] == ["opensubtitlescom", "podnapisi"]

    def test_should_enable_none_without_a_login(self, fake_server):
        providers(fake_server, "[]")

        bazarr(fake_server).use_providers()

        assert fake_server.requests == []

    def test_should_enable_none_without_the_opensubtitles_password(self, fake_server):
        providers(fake_server, "[]")

        bazarr(fake_server, "lucas", None).use_providers()

        assert fake_server.requests == []

    def test_should_enable_none_without_the_opensubtitles_username(self, fake_server):
        providers(fake_server, "[]")

        bazarr(fake_server, None, "opensubtitles-password").use_providers()

        assert fake_server.requests == []


class TestGivenFollow:
    def test_should_connect_radarr_by_its_container_name(self, fake_server):
        fake_server.routes[("POST", "/system/settings")] = Response(status=204)

        bazarr(fake_server).follow("radarr")

        assert form(fake_server) == {
            "settings-general-use_radarr": ["true"],
            "settings-radarr-ip": ["radarr"],
            "settings-radarr-port": ["7878"],
            "settings-radarr-base_url": ["/"],
            "settings-radarr-ssl": ["false"],
            "settings-radarr-apikey": ["radarr-key"],
        }

    def test_should_connect_sonarr_on_its_port(self, fake_server):
        fake_server.routes[("POST", "/system/settings")] = Response(status=204)

        bazarr(fake_server).follow("sonarr")

        assert form(fake_server)["settings-sonarr-port"] == ["8989"]
