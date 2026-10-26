from typing import Protocol


# Downloads the subtitles of what the media managers imported (Bazarr).
class SubtitleManager(Protocol):
    def prefer_portuguese(self) -> None: ...

    def use_providers(self) -> None: ...

    # app is the media manager by container name: radarr or sonarr.
    def follow(self, app: str) -> None: ...
