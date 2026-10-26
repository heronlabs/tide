from typing import Protocol

from tide.core.domain.wire_report import WireReport


# Wires the services together once (WireService).
class Wire(Protocol):
    def run(self) -> WireReport: ...
