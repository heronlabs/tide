import json

import pytest
from mocks.http_server import FakeServer, Response

from tide.infrastructure.arr.arr_service import ArrService
from tide.infrastructure.http.api_client import ApiClient


# Radarr at the FakeServer, with the values main gives it.
def radarr(server: FakeServer) -> ArrService:
    return ArrService(
        ApiClient(server.url, lambda: "radarr-key", 30, id_in_body=True, media_browser=False),
        root_folder="/data/movies",
        naming={"renameMovies": True, "movieFolderFormat": "{Movie Title} ({Release Year})"},
        category_field="movieCategory",
        category="radarr",
        quality_profile="HD-1080p",
        qbit_username="admin",
        qbit_password="qbit-password",
        jellyfin_api_key="jellyfin-key",
    )


# The parsed bodies of the requests the server got with this method and path.
def sent(server: FakeServer, method: str, path: str) -> list[object]:
    return [json.loads(request.body) for request in server.requests if (request.method, request.path) == (method, path)]


class TestGivenAddRootFolder:
    def test_should_add_the_root_folder(self, fake_server):
        fake_server.routes[("GET", "/rootfolder")] = Response(body='[{"id": 1, "path": "/data/downloads"}]')
        fake_server.routes[("POST", "/rootfolder")] = Response(body='{"id": 2, "path": "/data/movies"}')

        radarr(fake_server).add_root_folder()

        assert sent(fake_server, "POST", "/rootfolder") == [{"path": "/data/movies"}]

    def test_should_keep_the_root_folder_already_there(self, fake_server):
        fake_server.routes[("GET", "/rootfolder")] = Response(body='[{"id": 1, "path": "/data/movies"}]')

        radarr(fake_server).add_root_folder()

        assert sent(fake_server, "POST", "/rootfolder") == []


class TestGivenNameFiles:
    def test_should_put_the_naming_over_the_current_one(self, fake_server):
        fake_server.routes[("GET", "/config/naming")] = Response(
            body='{"id": 3, "renameMovies": false, "movieFolderFormat": "{Movie Title}",'
            ' "colonReplacementFormat": "smart"}'
        )
        fake_server.routes[("PUT", "/config/naming/3")] = Response(body="{}")

        radarr(fake_server).name_files()

        assert sent(fake_server, "PUT", "/config/naming/3") == [
            {
                "id": 3,
                "renameMovies": True,
                "movieFolderFormat": "{Movie Title} ({Release Year})",
                "colonReplacementFormat": "smart",
            }
        ]


class TestGivenPreferPortuguese:
    def test_should_add_the_language_custom_format_with_the_id_the_app_gives_it(self, fake_server):
        fake_server.routes[("GET", "/language")] = Response(
            body='[{"id": 1, "name": "English", "nameLower": "english"},'
            ' {"id": 30, "name": "Portuguese (Brazil)", "nameLower": "portuguese (brazil)"}]'
        )
        fake_server.routes[("GET", "/customformat")] = Response(body="[]")
        fake_server.routes[("POST", "/customformat")] = Response(body='{"id": 5, "name": "Portuguese (Brazil)"}')
        fake_server.routes[("GET", "/qualityprofile")] = Response(
            body='[{"id": 4, "name": "HD-1080p", "formatItems": [{"format": 5, "name": "Portuguese (Brazil)",'
            ' "score": 0}]}]'
        )
        fake_server.routes[("PUT", "/qualityprofile/4")] = Response(body="{}")

        radarr(fake_server).prefer_portuguese()

        assert sent(fake_server, "POST", "/customformat") == [
            {
                "name": "Portuguese (Brazil)",
                "includeCustomFormatWhenRenaming": False,
                "specifications": [
                    {
                        "name": "Portuguese (Brazil)",
                        "implementation": "LanguageSpecification",
                        "negate": False,
                        "required": True,
                        "fields": [{"name": "value", "value": 30}, {"name": "exceptLanguage", "value": False}],
                    }
                ],
            }
        ]

    def test_should_score_the_language_format_in_the_quality_profile(self, fake_server):
        fake_server.routes[("GET", "/language")] = Response(body='[{"id": 33, "name": "Portuguese (Brazil)"}]')
        fake_server.routes[("GET", "/customformat")] = Response(body="[]")
        fake_server.routes[("POST", "/customformat")] = Response(body='{"id": 5, "name": "Portuguese (Brazil)"}')
        fake_server.routes[("GET", "/qualityprofile")] = Response(
            body='[{"id": 1, "name": "Any", "formatItems": [{"format": 5, "name": "Portuguese (Brazil)", "score": 0}]},'
            ' {"id": 4, "name": "HD-1080p", "cutoff": 9, "formatItems": ['
            '{"format": 5, "name": "Portuguese (Brazil)", "score": 0}, {"format": 6, "name": "x265", "score": -10}]}]'
        )
        fake_server.routes[("PUT", "/qualityprofile/4")] = Response(body="{}")

        radarr(fake_server).prefer_portuguese()

        assert sent(fake_server, "PUT", "/qualityprofile/4") == [
            {
                "id": 4,
                "name": "HD-1080p",
                "cutoff": 9,
                "formatItems": [
                    {"format": 5, "name": "Portuguese (Brazil)", "score": 100},
                    {"format": 6, "name": "x265", "score": -10},
                ],
            }
        ]

    def test_should_fail_without_the_language(self, fake_server):
        fake_server.routes[("GET", "/language")] = Response(body='[{"id": 1, "name": "English"}]')

        with pytest.raises(OSError) as error:
            radarr(fake_server).prefer_portuguese()

        assert str(error.value) == "no name Portuguese (Brazil)"

    def test_should_fail_without_the_quality_profile(self, fake_server):
        fake_server.routes[("GET", "/language")] = Response(body='[{"id": 30, "name": "Portuguese (Brazil)"}]')
        fake_server.routes[("GET", "/customformat")] = Response(body="[]")
        fake_server.routes[("POST", "/customformat")] = Response(body='{"id": 5, "name": "Portuguese (Brazil)"}')
        fake_server.routes[("GET", "/qualityprofile")] = Response(body='[{"id": 1, "name": "Any", "formatItems": []}]')

        with pytest.raises(OSError) as error:
            radarr(fake_server).prefer_portuguese()

        assert str(error.value) == "no name HD-1080p"


class TestGivenUseQbittorrent:
    def test_should_add_qbittorrent_with_the_category_removing_what_it_imported(self, fake_server):
        fake_server.routes[("GET", "/downloadclient/schema")] = Response(
            body=json.dumps(
                [
                    {"implementation": "Transmission", "name": "", "fields": []},
                    {
                        "implementation": "QBittorrent",
                        "name": "",
                        "enable": False,
                        "protocol": "torrent",
                        "removeCompletedDownloads": False,
                        "removeFailedDownloads": False,
                        "fields": [
                            {"name": "host", "value": "localhost"},
                            {"name": "port", "value": 8090},
                            {"name": "username", "value": None},
                            {"name": "password", "value": None},
                            {"name": "movieCategory", "value": "movies"},
                            {"name": "sequentialOrder", "value": False},
                        ],
                    },
                ]
            )
        )
        fake_server.routes[("GET", "/downloadclient")] = Response(body="[]")
        fake_server.routes[("POST", "/downloadclient")] = Response(body="{}")

        radarr(fake_server).use_qbittorrent()

        assert sent(fake_server, "POST", "/downloadclient") == [
            {
                "implementation": "QBittorrent",
                "name": "qBittorrent",
                "enable": True,
                "protocol": "torrent",
                "removeCompletedDownloads": True,
                "removeFailedDownloads": True,
                "fields": [
                    {"name": "host", "value": "qbittorrent"},
                    {"name": "port", "value": 8080},
                    {"name": "username", "value": "admin"},
                    {"name": "password", "value": "qbit-password"},
                    {"name": "movieCategory", "value": "radarr"},
                    {"name": "sequentialOrder", "value": False},
                ],
            }
        ]


class TestGivenNotifyJellyfin:
    def test_should_connect_jellyfin_on_every_change_of_the_files(self, fake_server):
        fake_server.routes[("GET", "/notification/schema")] = Response(
            body=json.dumps(
                [
                    {"implementation": "PlexServer", "name": "", "fields": []},
                    {
                        "implementation": "MediaBrowser",
                        "name": "",
                        "onGrab": False,
                        "onDownload": False,
                        "onUpgrade": False,
                        "onRename": False,
                        "onMovieDelete": False,
                        "onMovieFileDelete": False,
                        "onHealthIssue": False,
                        "supportsOnDownload": True,
                        "fields": [
                            {"name": "host", "value": None},
                            {"name": "port", "value": 8920},
                            {"name": "useSsl", "value": False},
                            {"name": "apiKey", "value": None},
                            {"name": "notify", "value": False},
                            {"name": "updateLibrary", "value": False},
                            {"name": "mapFrom", "value": None},
                            {"name": "mapTo", "value": None},
                        ],
                    },
                ]
            )
        )
        fake_server.routes[("GET", "/notification")] = Response(body="[]")
        fake_server.routes[("POST", "/notification")] = Response(body="{}")

        radarr(fake_server).notify_jellyfin()

        assert sent(fake_server, "POST", "/notification") == [
            {
                "implementation": "MediaBrowser",
                "name": "Jellyfin",
                "onGrab": False,
                "onDownload": True,
                "onUpgrade": True,
                "onRename": True,
                "onMovieDelete": True,
                "onMovieFileDelete": True,
                "onHealthIssue": False,
                "supportsOnDownload": True,
                "fields": [
                    {"name": "host", "value": "jellyfin"},
                    {"name": "port", "value": 8096},
                    {"name": "useSsl", "value": False},
                    {"name": "apiKey", "value": "jellyfin-key"},
                    {"name": "notify", "value": False},
                    {"name": "updateLibrary", "value": True},
                    {"name": "mapFrom", "value": "/data/"},
                    {"name": "mapTo", "value": "/media/"},
                ],
            }
        ]


class TestGivenImportSubtitles:
    def test_should_import_the_srt_files_that_come_in_a_download(self, fake_server):
        fake_server.routes[("GET", "/config/mediamanagement")] = Response(
            body='{"id": 1, "importExtraFiles": false, "extraFileExtensions": "nfo", "recycleBin": ""}'
        )
        fake_server.routes[("PUT", "/config/mediamanagement/1")] = Response(body="{}")

        radarr(fake_server).import_subtitles()

        assert sent(fake_server, "PUT", "/config/mediamanagement/1") == [
            {"id": 1, "importExtraFiles": True, "extraFileExtensions": "srt", "recycleBin": ""}
        ]
