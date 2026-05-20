from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

@dataclass
class CycleResult:
    worker_id: str
    cycle: int

    target: Optional[str] = None
    target_id: Optional[str] = None
    source: Optional[str] = None  # fila_coleta, fallback, manual, dry_run

    extracted: int = 0
    normalized: int = 0
    inserted: int = 0
    duplicated: int = 0
    classified: int = 0
    audit_checked: int = 0
    failed: int = 0

    db_success: bool = False
    classifier_success: bool = False

    simulated: bool = False
    error: Optional[str] = None

    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        total = self.inserted + self.duplicated + self.failed
        if total <= 0:
            return 0.0
        return round(((self.inserted + self.duplicated) / total) * 100, 2)

    @property
    def is_real_collection(self) -> bool:
        return (
            not self.simulated
            and self.target is not None
            and self.extracted > 0
            and self.db_success
        )
