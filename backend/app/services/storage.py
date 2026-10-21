"""Local storage placeholder for Final-1 IpfsStorage.

Final-1 storage must keep AES-256-GCM ciphertext only, as specified in
docs/architecture/ipfs-ethereum-design.md.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from uuid import UUID

from app.services.hashing import sha256_bytes


class StorageBackend(ABC):
    """Interface for evidence storage backends."""

    @abstractmethod
    def save(self, evidence_id: str, extension: str, data: bytes) -> str:
        """Save evidence bytes and return a storage reference."""

    @abstractmethod
    def load(self, ref: str) -> bytes:
        """Load evidence bytes from a storage reference."""

    @abstractmethod
    def exists(self, ref: str) -> bool:
        """Return whether a storage reference points to an existing item."""

    def verify_stored(self, ref: str, expected_sha256: str) -> bool:
        """Compare stored bytes' SHA-256 digest with the expected digest."""
        return sha256_bytes(self.load(ref)) == expected_sha256


class LocalStorage(StorageBackend):
    """Store evidence files on local disk."""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir

    def save(self, evidence_id: str, extension: str, data: bytes) -> str:
        """Write evidence without overwriting an existing file."""
        try:
            UUID(evidence_id)
        except (AttributeError, ValueError) as exc:
            raise ValueError("evidence_id must be a valid UUID") from exc

        if (
            not extension.startswith(".")
            or not extension[1:].isascii()
            or not extension[1:].isalnum()
            or "/" in extension
            or "\\" in extension
        ):
            raise ValueError("extension must be a file extension")

        filename = f"{UUID(evidence_id)}{extension}"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        with (self.base_dir / filename).open("xb") as file_handle:
            file_handle.write(data)
        return filename

    def load(self, ref: str) -> bytes:
        """Read evidence bytes for a local storage reference."""
        return self._path_for_ref(ref).read_bytes()

    def exists(self, ref: str) -> bool:
        """Check whether a local storage reference is an existing file."""
        return self._path_for_ref(ref).is_file()

    def _path_for_ref(self, ref: str) -> Path:
        if (
            not ref
            or ref in {".", ".."}
            or "/" in ref
            or "\\" in ref
            or ":" in ref
            or Path(ref).name != ref
            or Path(ref).is_absolute()
        ):
            raise ValueError("Invalid local storage reference")
        return self.base_dir / ref
