"""Evidence data model for the Mid-1 backend."""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Evidence:
    """Metadata for an uploaded evidence item."""

    evidence_id: str
    case_id: Optional[str]
    filename: str
    extension: str
    size_bytes: int
    sha256_original: str
    sha256_copy: Optional[str]
    storage_ref: str
    ocr_status: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        """Return model fields as a JSON-friendly dictionary."""
        values = asdict(self)
        values["created_at"] = self.created_at.isoformat()
        return values
