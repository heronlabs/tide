from typing import Protocol


# Takes the requests of the users and sends them to the media managers (Seerr).
class RequestManager(Protocol):
    def send_to_radarr(self) -> None: ...

    def send_to_sonarr(self) -> None: ...

    # Leaves the library Discover of the media server out, whose placeholders are not available.
    def skip_discover(self) -> None: ...
