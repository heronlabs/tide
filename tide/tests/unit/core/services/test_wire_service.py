from tide.core.domain.failure import Failure
from tide.core.services.wire_service import WireService


class FakeMediaManager:
    def __init__(self, failing: str | None = None) -> None:
        self._failing = failing

    def add_root_folder(self) -> None:
        self._step("add_root_folder")

    def name_files(self) -> None:
        self._step("name_files")

    def prefer_portuguese(self) -> None:
        self._step("prefer_portuguese")

    def use_qbittorrent(self) -> None:
        self._step("use_qbittorrent")

    def notify_jellyfin(self) -> None:
        self._step("notify_jellyfin")

    def import_subtitles(self) -> None:
        self._step("import_subtitles")

    def _step(self, name: str) -> None:
        if name == self._failing:
            raise ConnectionRefusedError("Connection refused")


class FakeIndexers:
    def __init__(self) -> None:
        self.synced: list[str] = []

    def sync(self, app: str) -> None:
        self.synced.append(app)


class FakeRequests:
    def send_to_radarr(self) -> None:
        pass

    def send_to_sonarr(self) -> None:
        pass

    def skip_discover(self) -> None:
        pass


class FakeSubtitles:
    def __init__(self) -> None:
        self.followed: list[str] = []

    def prefer_portuguese(self) -> None:
        pass

    def use_providers(self) -> None:
        pass

    def follow(self, app: str) -> None:
        self.followed.append(app)


class FakeMediaServer:
    def add_repository(self) -> None:
        pass

    def bridge_seerr(self) -> None:
        pass

    def add_discover(self) -> None:
        pass


class TestGivenRun:
    def test_should_do_every_step_in_order(self):
        wire = WireService(
            FakeMediaManager(), FakeMediaManager(), FakeIndexers(), FakeRequests(), FakeSubtitles(), FakeMediaServer()
        )

        report = wire.run()

        assert report.done == [
            "radarr: root folder",
            "radarr: naming",
            "radarr: Portuguese (Brazil)",
            "radarr: qBittorrent",
            "radarr: Jellyfin",
            "radarr: subtitles",
            "sonarr: root folder",
            "sonarr: naming",
            "sonarr: Portuguese (Brazil)",
            "sonarr: qBittorrent",
            "sonarr: Jellyfin",
            "sonarr: subtitles",
            "prowlarr: radarr",
            "prowlarr: sonarr",
            "seerr: radarr",
            "seerr: sonarr",
            "jellyfin: repository",
            "jellyfin: JellyBridge",
            "jellyfin: Discover",
            "seerr: libraries",
            "bazarr: Portuguese (Brazil)",
            "bazarr: providers",
            "bazarr: radarr",
            "bazarr: sonarr",
        ]

    def test_should_sync_radarr_then_sonarr_to_the_indexers(self):
        indexers = FakeIndexers()

        WireService(
            FakeMediaManager(), FakeMediaManager(), indexers, FakeRequests(), FakeSubtitles(), FakeMediaServer()
        ).run()

        assert indexers.synced == ["radarr", "sonarr"]

    def test_should_have_bazarr_follow_radarr_then_sonarr(self):
        subtitles = FakeSubtitles()

        WireService(
            FakeMediaManager(), FakeMediaManager(), FakeIndexers(), FakeRequests(), subtitles, FakeMediaServer()
        ).run()

        assert subtitles.followed == ["radarr", "sonarr"]

    def test_should_report_the_step_that_failed_and_why(self):
        wire = WireService(
            FakeMediaManager(),
            FakeMediaManager(failing="prefer_portuguese"),
            FakeIndexers(),
            FakeRequests(),
            FakeSubtitles(),
            FakeMediaServer(),
        )

        report = wire.run()

        assert report.failed == [Failure("sonarr: Portuguese (Brazil)", "Connection refused")]

    def test_should_go_on_after_a_step_that_failed(self):
        wire = WireService(
            FakeMediaManager(failing="add_root_folder"),
            FakeMediaManager(),
            FakeIndexers(),
            FakeRequests(),
            FakeSubtitles(),
            FakeMediaServer(),
        )

        report = wire.run()

        assert report.done[:2] == ["radarr: naming", "radarr: Portuguese (Brazil)"]
