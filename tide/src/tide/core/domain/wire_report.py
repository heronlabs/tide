from dataclasses import dataclass, field

from tide.core.domain.failure import Failure


# What one wire did: the steps done and the steps that failed, in the order they ran.
@dataclass
class WireReport:
    done: list[str] = field(default_factory=list)
    failed: list[Failure] = field(default_factory=list)
