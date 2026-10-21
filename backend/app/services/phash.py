"""Perceptual hashing (pHash) for image evidence — FYP-1 Mid prototype.

Why pHash next to SHA-256
  SHA-256 (app/services/hashing.py) answers "are these the exact same bytes?". Any re-save,
  resize or recompression gives a completely different SHA-256, even when the picture looks
  identical. pHash answers a different question: "do these two images LOOK the same?".
  It lets FardNama recognise that two uploads are copies of one screenshot (forwarded,
  compressed by WhatsApp, resized) and link them in a case.

How it works (the standard DCT pHash)
  1. Convert to grayscale and shrink to (4 x hash_size) pixels square, removing detail and colour.
  2. Run a 2-D Discrete Cosine Transform (DCT): it describes the image as a mix of
     patterns from coarse (low frequency) to fine (high frequency).
  3. Keep only the top-left hash_size x hash_size block = the coarsest patterns,
     i.e. the overall structure of the picture.
  4. Each value becomes one bit: 1 if above the median of the block, else 0.
  5. The bits are written as a hex string.
  Two images are compared by the Hamming distance between their hashes (how many bits
  differ). The verdict uses the distance as a FRACTION of all bits, so the same rule
  works for 64-bit (hash_size=8) and 256-bit (hash_size=16) hashes.

Hash size
  hash_size=8 (64 bits) is the textbook default. On our synthetic chat screenshots, every
  chat looks alike at 64 bits because the app layout (header, bubbles, background) dominates.
  hash_size=16 (256 bits) separated true copies (0-1% of bits) from a different conversation
  (~20%) more clearly, so FardNama uses 16 by default. Both sizes are supported.

Limits (state these in the report and demo)
  - pHash measures visual similarity. It does NOT prove that an image was or was not
    manipulated, and a small local edit (one changed message) keeps the hash close.
    Byte-level tampering is SHA-256's job; local edits are what ELA looks at.
  - Large crops, rotations, mirroring and strong brightness changes move the hash a lot.
  - Different screenshots from the same chat app look partly similar (shared layout).
  - Thresholds below are prototype starting points and must be tuned on real samples.

The DCT is written in plain Python (only Pillow is needed). The bit layout matches the
widely used `imagehash.phash(image, hash_size=N)`, so results can be cross-checked.
"""
from __future__ import annotations

import io
import math
from dataclasses import asdict, dataclass
from functools import lru_cache

from PIL import Image, ImageOps, UnidentifiedImageError

DEFAULT_HASH_SIZE = 16             # 16 x 16 = 256-bit hash (see "Hash size" above)
HIGHFREQ_FACTOR = 4                # image is shrunk to (hash_size * 4) square before the DCT

# Prototype thresholds, as a fraction of differing bits.
# <= 10%: very likely the same picture (re-saved, resized, compressed)
NEAR_DUPLICATE_MAX_FRACTION = 0.10
# <= 25%: possibly related (cropped, edited, same app layout) -> a person reviews
RELATED_MAX_FRACTION = 0.25
#  > 25%: different images


@dataclass(frozen=True)
class PHashComparison:
    hash_a: str
    hash_b: str
    hash_bits: int         # 64 or 256
    distance: int          # Hamming distance: number of differing bits
    distance_fraction: float
    similarity: float      # 1 - distance_fraction
    verdict: str           # near_duplicate | possibly_related | different

    def to_dict(self) -> dict:
        return asdict(self)


@lru_cache(maxsize=4)
def _dct_rows(hash_size: int) -> tuple[tuple[float, ...], ...]:
    """First hash_size rows of the DCT-II basis: row[k][n] = cos(pi * (2n + 1) * k / (2N))."""
    n_pixels = hash_size * HIGHFREQ_FACTOR
    return tuple(
        tuple(math.cos(math.pi * (2 * n + 1) * k / (2 * n_pixels)) for n in range(n_pixels))
        for k in range(hash_size)
    )


def _load_grayscale(image_bytes: bytes) -> Image.Image:
    if not isinstance(image_bytes, (bytes, bytearray)) or not image_bytes:
        raise ValueError("Expected non-empty image bytes.")
    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            image.load()
            image = ImageOps.exif_transpose(image)   # respect phone camera orientation
            return image.convert("L")
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("Invalid or unreadable image bytes.") from exc


def phash_from_image(image: Image.Image, hash_size: int = DEFAULT_HASH_SIZE) -> str:
    """Perceptual hash of a PIL image as lowercase hex (hash_size**2 bits)."""
    if hash_size < 2:
        raise ValueError("hash_size must be at least 2.")
    n_pixels = hash_size * HIGHFREQ_FACTOR
    dct = _dct_rows(hash_size)
    small = image.convert("L").resize((n_pixels, n_pixels), Image.Resampling.LANCZOS)
    # mode "L": one byte (0-255) per pixel; works on all Pillow versions
    pixels = list(small.tobytes())
    rows = [pixels[r * n_pixels:(r + 1) * n_pixels] for r in range(n_pixels)]

    # 2-D DCT, low-frequency block only:  low = D * X * D^T  (D = first hash_size DCT rows)
    tmp = [[sum(dct[k][n] * rows[n][c] for n in range(n_pixels)) for c in range(n_pixels)]
           for k in range(hash_size)]
    low = [[sum(tmp[k][m] * dct[j][m] for m in range(n_pixels)) for j in range(hash_size)]
           for k in range(hash_size)]

    values = [v for row in low for v in row]
    n_bits = len(values)
    ordered = sorted(values)
    median = (ordered[n_bits // 2 - 1] + ordered[n_bits // 2]) / 2
    bits = "".join("1" if v > median else "0" for v in values)
    return f"{int(bits, 2):0{(n_bits + 3) // 4}x}"


def phash_bytes(image_bytes: bytes, hash_size: int = DEFAULT_HASH_SIZE) -> str:
    """Perceptual hash of image bytes (PNG, JPEG, WebP, BMP, TIFF).

    Raises ValueError on bad input.
    """
    return phash_from_image(_load_grayscale(image_bytes), hash_size)


def hamming_distance(hash_a: str, hash_b: str) -> int:
    """Number of differing bits between two hex pHash strings of the same size."""
    if len(hash_a) != len(hash_b):
        raise ValueError("Hashes must have the same length (same hash_size).")
    return bin(int(hash_a, 16) ^ int(hash_b, 16)).count("1")


def verdict_for(distance_fraction: float) -> str:
    if distance_fraction <= NEAR_DUPLICATE_MAX_FRACTION:
        return "near_duplicate"
    if distance_fraction <= RELATED_MAX_FRACTION:
        return "possibly_related"
    return "different"


def compare_hashes(hash_a: str, hash_b: str) -> PHashComparison:
    bits = len(hash_a) * 4
    distance = hamming_distance(hash_a, hash_b)
    fraction = distance / bits
    return PHashComparison(
        hash_a=hash_a,
        hash_b=hash_b,
        hash_bits=bits,
        distance=distance,
        distance_fraction=round(fraction, 4),
        similarity=round(1 - fraction, 4),
        verdict=verdict_for(fraction),
    )


def compare_images(
        image_a: bytes,
        image_b: bytes,
        hash_size: int = DEFAULT_HASH_SIZE) -> PHashComparison:
    """Hash two images and report how visually similar they are."""
    return compare_hashes(phash_bytes(image_a, hash_size), phash_bytes(image_b, hash_size))
