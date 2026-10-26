from typing import Protocol


# Plays the library and shows Seerr's catalog in it through the plugin JellyBridge (Jellyfin).
class MediaServer(Protocol):
    def add_repository(self) -> None: ...

    def bridge_seerr(self) -> None: ...

    def add_discover(self) -> None: ...
