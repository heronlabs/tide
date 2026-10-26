import re
from collections.abc import Mapping

from tide.infrastructure.http.api_client import ApiClient
from tide.infrastructure.http.schema import find, with_values

# The events of the Jellyfin connection that change files: Radarr's onMovieDelete, Sonarr's onEpisodeFileDelete...
EVENTS = re.compile(r"on(Download|Upgrade|Rename|.*Delete)")
# The language whose releases win over the others of a quality, by the name Radarr and Sonarr both give it: each
# numbers its languages its own way, so the id is read from the app.
PORTUGUESE = "Portuguese (Brazil)"


# Radarr or Sonarr, which share their API v3: where and how it imports, the Portuguese (Brazil) preference,
# qBittorrent as its download client, Jellyfin as its connection and the subtitles that come in a download. Every
# address is the container name on the network tide.
class ArrService:
    def __init__(
        self,
        client: ApiClient,
        root_folder: str,
        naming: Mapping[str, object],
        category_field: str,
        category: str,
        quality_profile: str,
        qbit_username: str,
        qbit_password: str,
        jellyfin_api_key: str,
    ) -> None:
        self._client = client
        self._root_folder = root_folder
        self._naming = naming
        self._category_field = category_field
        self._category = category
        self._quality_profile = quality_profile
        self._qbit_username = qbit_username
        self._qbit_password = qbit_password
        self._jellyfin_api_key = jellyfin_api_key

    def add_root_folder(self) -> None:
        if all(folder["path"] != self._root_folder for folder in self._client.get("/rootfolder")):
            self._client.post("/rootfolder", {"path": self._root_folder})

    def name_files(self) -> None:
        naming = self._client.get("/config/naming")
        self._client.put(f"/config/naming/{naming['id']}", {**naming, **self._naming})

    def prefer_portuguese(self) -> None:
        language = find(self._client.get("/language"), "name", PORTUGUESE)
        specification = {
            "name": PORTUGUESE,
            "implementation": "LanguageSpecification",
            "negate": False,
            "required": True,
            "fields": [{"name": "value", "value": language["id"]}, {"name": "exceptLanguage", "value": False}],
        }
        custom_format = {
            "name": PORTUGUESE,
            "includeCustomFormatWhenRenaming": False,
            "specifications": [specification],
        }
        saved = self._client.upsert("/customformat", custom_format)
        profile = find(self._client.get("/qualityprofile"), "name", self._quality_profile)
        items = [{**item, "score": 100} if item["format"] == saved["id"] else item for item in profile["formatItems"]]
        self._client.put(f"/qualityprofile/{profile['id']}", {**profile, "formatItems": items})

    # The category is the container name (radarr, sonarr), which tells their torrents apart in qBittorrent.
    def use_qbittorrent(self) -> None:
        schema = find(self._client.get("/downloadclient/schema"), "implementation", "QBittorrent")
        values = {
            "host": "qbittorrent",
            "port": 8080,
            "username": self._qbit_username,
            "password": self._qbit_password,
            self._category_field: self._category,
        }
        download_client = {
            **schema,
            "name": "qBittorrent",
            "enable": True,
            "removeCompletedDownloads": True,
            "removeFailedDownloads": True,
            "fields": with_values(schema["fields"], values),
        }
        self._client.upsert("/downloadclient", download_client)

    # Jellyfin mounts ~/Media at /media, where Radarr and Sonarr see /data.
    def notify_jellyfin(self) -> None:
        schema = find(self._client.get("/notification/schema"), "implementation", "MediaBrowser")
        values = {
            "host": "jellyfin",
            "port": 8096,
            "apiKey": self._jellyfin_api_key,
            "updateLibrary": True,
            "mapFrom": "/data/",
            "mapTo": "/media/",
        }
        events = {name: True for name in schema if EVENTS.match(name)}
        notification = {**schema, **events, "name": "Jellyfin", "fields": with_values(schema["fields"], values)}
        self._client.upsert("/notification", notification)

    # A subtitle that comes in the torrent next to the video is imported with it, named like it.
    def import_subtitles(self) -> None:
        management = self._client.get("/config/mediamanagement")
        extra_files = {"importExtraFiles": True, "extraFileExtensions": "srt"}
        self._client.put(f"/config/mediamanagement/{management['id']}", {**management, **extra_files})
