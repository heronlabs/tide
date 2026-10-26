from dataclasses import dataclass


# One step that could not be done, and why.
@dataclass(frozen=True)
class Failure:
    step: str
    reason: str
