from dataclasses import dataclass
from enum import StrEnum


class Decision(StrEnum):
    ALLOW = "allow"
    BLOCK = "block"


@dataclass(frozen=True)
class GuardResult:
    decision: Decision
    layer: str
    reason: str
    score: float | None = None

    @property
    def allowed(self) -> bool:
        return self.decision == Decision.ALLOW
