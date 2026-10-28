from typing import Protocol


# Downloads the torrents the media managers send it (qBittorrent).
class DownloadClient(Protocol):
    def skip_slow_torrents(self) -> None: ...
