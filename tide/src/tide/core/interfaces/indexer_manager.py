from typing import Protocol


# Manages the indexers and syncs them to the media managers (Prowlarr).
class IndexerManager(Protocol):
    # app is the media manager by container name: radarr or sonarr.
    def sync(self, app: str) -> None: ...
