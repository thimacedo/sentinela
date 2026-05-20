from dataclasses import dataclass
from typing import Optional

@dataclass
class Target:
    username: str
    candidato_id: Optional[str] = None
    queue_id: Optional[str] = None
    source: str = "unknown"