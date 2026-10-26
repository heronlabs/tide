# Create the dependency injection for the commands.
# `tide wire` wires the running services together through their APIs.
import argparse
import sys
from functools import partial

from tide.application.cli.wire_command import WireCommand
from tide.core.services.wire_service import WireService
from tide.infrastructure.arr.arr_service import ArrService
from tide.infrastructure.bazarr.bazarr_service import BazarrService
from tide.infrastructure.docker.key_service import KeyService
from tide.infrastructure.environment.environment_service import EnvironmentService
from tide.infrastructure.http.api_client import ApiClient
from tide.infrastructure.jellyfin.jellyfin_service import JellyfinService
from tide.infrastructure.prowlarr.prowlarr_service import ProwlarrService
from tide.infrastructure.seerr.seerr_service import SeerrService

TIMEOUT = 30


def build_wire_command(environment: EnvironmentService) -> WireCommand:
    keys = KeyService(
        {
            "radarr": environment.radarr_api_key,
            "sonarr": environment.sonarr_api_key,
            "prowlarr": environment.prowlarr_api_key,
            "seerr": environment.seerr_api_key,
            "bazarr": environment.bazarr_api_key,
        },
        docker="docker",
    )
    common = {
        "quality_profile": environment.quality_profile,
        "qbit_username": environment.qbit_username,
        "qbit_password": environment.qbit_password,
        "jellyfin_api_key": environment.jellyfin_api_key,
    }
    radarr = ArrService(
        ApiClient(
            f"{environment.radarr_url}/api/v3",
            partial(keys.key, "radarr"),
            TIMEOUT,
            id_in_body=True,
            media_browser=False,
        ),
        root_folder="/data/movies",
        naming={
            "renameMovies": True,
            "standardMovieFormat": "{Movie Title} ({Release Year})",
            "movieFolderFormat": "{Movie Title} ({Release Year})",
        },
        category_field="movieCategory",
        category="radarr",
        **common,
    )
    sonarr = ArrService(
        ApiClient(
            f"{environment.sonarr_url}/api/v3",
            partial(keys.key, "sonarr"),
            TIMEOUT,
            id_in_body=True,
            media_browser=False,
        ),
        root_folder="/data/shows",
        naming={
            "renameEpisodes": True,
            "standardEpisodeFormat": "{Series TitleYear} - S{season:00}E{episode:00}",
            "animeEpisodeFormat": "{Series TitleYear} - S{season:00}E{episode:00}",
            "dailyEpisodeFormat": "{Series TitleYear} - {Air-Date}",
            "seriesFolderFormat": "{Series TitleYear}",
            "seasonFolderFormat": "Season {season:00}",
        },
        category_field="tvCategory",
        category="sonarr",
        **common,
    )
    prowlarr = ProwlarrService(
        ApiClient(
            f"{environment.prowlarr_url}/api/v1",
            partial(keys.key, "prowlarr"),
            TIMEOUT,
            id_in_body=True,
            media_browser=False,
        ),
        key_of=keys.key,
    )
    seerr = SeerrService(
        ApiClient(
            f"{environment.seerr_url}/api/v1",
            partial(keys.key, "seerr"),
            TIMEOUT,
            id_in_body=False,
            media_browser=False,
        ),
        key_of=keys.key,
        quality_profile=environment.quality_profile,
        lan_host=environment.lan_host,
    )
    bazarr = BazarrService(
        ApiClient(
            f"{environment.bazarr_url}/api", partial(keys.key, "bazarr"), TIMEOUT, id_in_body=False, media_browser=False
        ),
        key_of=keys.key,
        opensubtitles_username=environment.opensubtitles_username,
        opensubtitles_password=environment.opensubtitles_password,
    )
    jellyfin = JellyfinService(
        ApiClient(
            environment.jellyfin_url,
            lambda: environment.jellyfin_api_key,
            TIMEOUT,
            id_in_body=False,
            media_browser=True,
        ),
        key_of=keys.key,
    )
    wire = WireService(
        radarr=radarr, sonarr=sonarr, indexers=prowlarr, requests=seerr, subtitles=bazarr, media_server=jellyfin
    )
    return WireCommand(wire=wire)


def run() -> int:
    parser = argparse.ArgumentParser(prog="tide", description="Wires the tide media server services together.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("wire", help="wire Radarr, Sonarr, Prowlarr, Seerr, Bazarr and Jellyfin through their APIs")
    parser.parse_args()
    return build_wire_command(EnvironmentService.from_env()).execute()


if __name__ == "__main__":
    sys.exit(run())
