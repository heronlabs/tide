from tide.application.cli.wire_command import WireCommand
from tide.core.domain.failure import Failure
from tide.core.domain.wire_report import WireReport


class FakeWire:
    def __init__(self, report: WireReport) -> None:
        self._report = report

    def run(self) -> WireReport:
        return self._report


class TestGivenExecute:
    def test_should_print_each_step_and_the_summary(self, capsys):
        report = WireReport(
            done=["radarr: root folder"],
            failed=[Failure("sonarr: root folder", "Connection refused")],
        )

        WireCommand(FakeWire(report)).execute()

        assert capsys.readouterr().out == (
            "done   radarr: root folder\nfailed sonarr: root folder: Connection refused\nwire: 1 done, 1 failed\n"
        )

    def test_should_return_zero_when_nothing_failed(self):
        report = WireReport(done=["radarr: root folder"])

        assert WireCommand(FakeWire(report)).execute() == 0

    def test_should_return_one_when_a_step_failed(self):
        report = WireReport(done=["radarr: root folder"], failed=[Failure("sonarr: root folder", "Connection refused")])

        assert WireCommand(FakeWire(report)).execute() == 1
