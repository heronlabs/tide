from tide.core.interfaces.wire import Wire


# Run one wire and turn its report into output and the exit code for main.
class WireCommand:
    def __init__(self, wire: Wire) -> None:
        self._wire = wire

    def execute(self) -> int:
        report = self._wire.run()

        for step in report.done:
            print(f"done   {step}")
        for failure in report.failed:
            print(f"failed {failure.step}: {failure.reason}")

        print(f"wire: {len(report.done)} done, {len(report.failed)} failed")

        return 1 if report.failed else 0
