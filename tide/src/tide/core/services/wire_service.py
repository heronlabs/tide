from collections.abc import Callable

from tide.core.domain.failure import Failure
from tide.core.domain.wire_report import WireReport
from tide.core.interfaces.indexer_manager import IndexerManager
from tide.core.interfaces.media_manager import MediaManager
from tide.core.interfaces.media_server import MediaServer
from tide.core.interfaces.request_manager import RequestManager
from tide.core.interfaces.subtitle_manager import SubtitleManager


# Wire Radarr and Sonarr to the library, qBittorrent and Jellyfin, then Prowlarr, Seerr and Bazarr to them, and
# Jellyfin's library Discover to Seerr.
# A step that fails is reported and the next one still runs, so one service down does not hide the others.
class WireService:
    def __init__(
        self,
        radarr: MediaManager,
        sonarr: MediaManager,
        indexers: IndexerManager,
        requests: RequestManager,
        subtitles: SubtitleManager,
        media_server: MediaServer,
    ) -> None:
        self._radarr = radarr
        self._sonarr = sonarr
        self._indexers = indexers
        self._requests = requests
        self._subtitles = subtitles
        self._media_server = media_server

    def run(self) -> WireReport:
        report = WireReport()
        for step, action in self._steps():
            try:
                action()
                report.done.append(step)
            except OSError as error:
                report.failed.append(Failure(step, str(error)))
        return report

    def _steps(self) -> list[tuple[str, Callable[[], None]]]:
        return [
            *_media_steps("radarr", self._radarr),
            *_media_steps("sonarr", self._sonarr),
            ("prowlarr: radarr", lambda: self._indexers.sync("radarr")),
            ("prowlarr: sonarr", lambda: self._indexers.sync("sonarr")),
            ("seerr: radarr", self._requests.send_to_radarr),
            ("seerr: sonarr", self._requests.send_to_sonarr),
            ("jellyfin: repository", self._media_server.add_repository),
            ("jellyfin: JellyBridge", self._media_server.bridge_seerr),
            ("jellyfin: Discover", self._media_server.add_discover),
            ("seerr: libraries", self._requests.skip_discover),
            ("bazarr: Portuguese (Brazil)", self._subtitles.prefer_portuguese),
            ("bazarr: providers", self._subtitles.use_providers),
            ("bazarr: radarr", lambda: self._subtitles.follow("radarr")),
            ("bazarr: sonarr", lambda: self._subtitles.follow("sonarr")),
        ]


def _media_steps(name: str, manager: MediaManager) -> list[tuple[str, Callable[[], None]]]:
    return [
        (f"{name}: root folder", manager.add_root_folder),
        (f"{name}: naming", manager.name_files),
        (f"{name}: Portuguese (Brazil)", manager.prefer_portuguese),
        (f"{name}: qBittorrent", manager.use_qbittorrent),
        (f"{name}: Jellyfin", manager.notify_jellyfin),
        (f"{name}: subtitles", manager.import_subtitles),
    ]
