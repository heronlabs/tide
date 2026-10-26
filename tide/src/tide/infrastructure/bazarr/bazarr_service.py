import json
from collections.abc import Callable

from tide.infrastructure.http.api_client import ApiClient

SETTINGS = "/system/settings"
# The language profile of every movie and episode: Portuguese (Brazil), Bazarr's code pb, not hearing impaired nor
# forced, wanted even when the audio is Portuguese too.
PROFILE = {
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
}
# OpenSubtitles.com, the one provider tide enables, with a free account.
PROVIDER = "opensubtitlescom"
PORTS = {"radarr": 7878, "sonarr": 8989}


# Bazarr: follows the movies of Radarr and the episodes of Sonarr and downloads their Portuguese (Brazil) subtitles
# from OpenSubtitles.com when given its login. Bazarr takes its settings as a form, and replaces the languages, the
# profiles and the providers whole, so each step sends the ones it has with tide's added.
class BazarrService:
    def __init__(
        self,
        client: ApiClient,
        key_of: Callable[[str], str],
        opensubtitles_username: str | None,
        opensubtitles_password: str | None,
    ) -> None:
        self._client = client
        self._key_of = key_of
        self._opensubtitles_username = opensubtitles_username
        self._opensubtitles_password = opensubtitles_password

    # The profile is the default of the movies and the shows, so Bazarr searches what it syncs from then on.
    def prefer_portuguese(self) -> None:
        profiles = self._client.get("/system/languages/profiles")
        ids = [profile["profileId"] for profile in profiles if profile["name"] == PROFILE["name"]]
        profile_id = ids[0] if ids else max([profile["profileId"] for profile in profiles], default=0) + 1
        others = [profile for profile in profiles if profile["profileId"] != profile_id]
        languages = [language["code2"] for language in self._client.get("/system/languages") if language["enabled"]]
        fields = {
            "languages-enabled": sorted({*languages, "pb"}),
            "languages-profiles": json.dumps([*others, {**PROFILE, "profileId": profile_id}]),
            "settings-general-movie_default_enabled": "true",
            "settings-general-movie_default_profile": str(profile_id),
            "settings-general-serie_default_enabled": "true",
            "settings-general-serie_default_profile": str(profile_id),
        }
        self._client.post_form(SETTINGS, fields)

    def use_providers(self) -> None:
        if not (self._opensubtitles_username and self._opensubtitles_password):
            return
        enabled = self._client.get(SETTINGS)["general"]["enabled_providers"]
        fields = {
            "settings-general-enabled_providers": enabled if PROVIDER in enabled else [*enabled, PROVIDER],
            "settings-opensubtitlescom-username": self._opensubtitles_username,
            "settings-opensubtitlescom-password": self._opensubtitles_password,
        }
        self._client.post_form(SETTINGS, fields)

    # Bazarr reaches the app by container name and sees its files at the same /data, so no path is mapped.
    def follow(self, app: str) -> None:
        fields = {
            f"settings-general-use_{app}": "true",
            f"settings-{app}-ip": app,
            f"settings-{app}-port": str(PORTS[app]),
            f"settings-{app}-base_url": "/",
            f"settings-{app}-ssl": "false",
            f"settings-{app}-apikey": self._key_of(app),
        }
        self._client.post_form(SETTINGS, fields)
