"""Error Level Analysis (ELA) for image evidence — FYP-1 Mid prototype.

Idea
  A JPEG loses a little detail every time it is saved. If the whole picture has been saved the
  same number of times, re-saving it once more changes every area by a similar, small amount.
  An area pasted or redrawn later has been compressed fewer times, so it usually changes MORE
  when re-saved. ELA re-saves the image at a known JPEG quality and shows, pixel by pixel, how
  much each area changed (the "error level").

What this module returns
  - ela image:   the per-pixel difference, brightened so it is visible
  - heatmap:     the difference averaged over small blocks and laid over the picture, so areas
                 that changed more stand out (yellow = more change)
  - numbers:     mean / 99th-percentile / max error and the brightest blocks to look at

Limits (state these in the report and demo)
  - ELA does NOT prove manipulation. It points a person at areas worth a closer look.
  - Sharp edges, text and strongly coloured areas always show higher error, edited or not.
    Judge a bright area against similar content in the same image (e.g. other chat bubbles).
  - Works best on JPEG images. PNG screenshots are lossless, so there is no compression history
    to compare and the output says so.
  - Heavy recompression (e.g. an image forwarded several times through a messaging app) can
    erase the traces of an edit.
Only Pillow is needed.
"""
from __future__ import annotations

import io
from dataclasses import asdict, dataclass, field

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError

DEFAULT_QUALITY = 90       # JPEG quality used for the re-save
DEFAULT_BLOCK = 16         # block size (pixels) for the heatmap and the "brightest blocks" list
DISPLAY_PERCENTILE = 99.5  # brighten the ELA image so this percentile maps to full white


@dataclass
class ELAResult:
    width: int
    height: int
    input_format: str
    quality: int
    mean_error: float          # average change per pixel, 0-255 scale
    p99_error: float           # 99% of pixels changed by at most this much
    max_error: int
    block_size: int
    brightest_blocks: list = field(default_factory=list)   # [{x, y, w, h, mean_error}]
    note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def load_rgb(image_bytes: bytes) -> tuple[Image.Image, str]:
    if not isinstance(image_bytes, (bytes, bytearray)) or not image_bytes:
        raise ValueError("Expected non-empty image bytes.")
    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            fmt = (image.format or "unknown").upper()
            image.load()
            image = ImageOps.exif_transpose(image)
            return image.convert("RGB"), fmt
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("Invalid or unreadable image bytes.") from exc


def _resave_jpeg(image: Image.Image, quality: int) -> Image.Image:
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=quality)
    return Image.open(io.BytesIO(buffer.getvalue())).convert("RGB")


def _percentile(gray: Image.Image, pct: float) -> int:
    hist = gray.histogram()
    target, running = sum(hist) * pct / 100, 0
    for value, count in enumerate(hist):
        running += count
        if running >= target:
            return value
    return 255


def error_level(image: Image.Image, quality: int = DEFAULT_QUALITY) -> Image.Image:
    """Grayscale image of how much each pixel changed after one JPEG re-save (0-255)."""
    if not 50 <= quality <= 99:
        raise ValueError("quality must be between 50 and 99.")
    return ImageChops.difference(image, _resave_jpeg(image, quality)).convert("L")


def ela_visual(diff: Image.Image) -> Image.Image:
    """Brighten the raw difference so it can be seen (differences are usually only a few levels)."""
    top = max(_percentile(diff, DISPLAY_PERCENTILE), 1)
    return diff.point(lambda v: min(255, v * 255 // top)).convert("RGB")


def block_means(diff: Image.Image, block: int = DEFAULT_BLOCK) -> Image.Image:
    """Average error per block (one pixel per block)."""
    cols, rows = max(diff.width // block, 1), max(diff.height // block, 1)
    return diff.crop((0, 0, cols * block, rows * block)).resize((cols, rows), Image.Resampling.BOX)


def heatmap(image: Image.Image, diff: Image.Image, block: int = DEFAULT_BLOCK) -> Image.Image:
    """Block-averaged error as black -> red -> yellow, laid over a grey copy of the picture."""
    small = block_means(diff, block)
    top = max(_percentile(small, 99), 1)
    small = small.point(lambda v: min(255, v * 255 // top))
    coloured = ImageOps.colorize(small, black="black", mid="red", white="yellow")
    coloured = coloured.resize(
        (small.width * block,
         small.height * block),
        Image.Resampling.NEAREST)
    canvas = Image.new("RGB", image.size, "black")
    canvas.paste(coloured, (0, 0))
    return Image.blend(image.convert("L").convert("RGB"), canvas, 0.6)


def region_mean(diff: Image.Image, box: tuple[int, int, int, int]) -> float:
    """Average error inside a box (x0, y0, x1, y1).

    Used to validate the prototype on known edits.
    """
    region = diff.crop(box)
    hist = region.histogram()
    total = sum(hist)
    return sum(v * c for v, c in enumerate(hist)) / total if total else 0.0


def analyse(
        image_bytes: bytes,
        quality: int = DEFAULT_QUALITY,
        block: int = DEFAULT_BLOCK,
        top_n: int = 5):
    """Run ELA. Returns (ELAResult, original RGB image, ela image, heatmap image)."""
    image, fmt = load_rgb(image_bytes)
    diff = error_level(image, quality)

    hist = diff.histogram()
    total = sum(hist)
    small = block_means(diff, block)
    cells = sorted(
        ((value, i % small.width, i // small.width) for i, value in enumerate(small.tobytes())),
        reverse=True,
    )[:top_n]

    note = ("Bright areas are worth a closer look; they are not proof of editing. "
            "Compare them with similar content in the same image.")
    if fmt != "JPEG":
        note = (f"Input is {fmt}, not JPEG: a lossless image has no compression history, so ELA "
                "mostly shows edges and colours here. " + note)

    result = ELAResult(
        width=image.width,
        height=image.height,
        input_format=fmt,
        quality=quality,
        mean_error=round(sum(v * c for v, c in enumerate(hist)) / total, 3),
        p99_error=float(_percentile(diff, 99)),
        max_error=diff.getextrema()[1],
        block_size=block,
        brightest_blocks=[
            {"x": cx * block, "y": cy * block, "w": block, "h": block, "mean_error": value}
            for value, cx, cy in cells
        ],
        note=note,
    )
    return result, image, ela_visual(diff), heatmap(image, diff, block)


def panel(original: Image.Image, ela_image: Image.Image, heat: Image.Image) -> Image.Image:
    """Original | ELA | heatmap side by side, with captions, for screenshots and the API."""
    w, h = original.size
    caption = 36
    out = Image.new("RGB", (w * 3, h + caption), "white")
    draw = ImageDraw.Draw(out)
    try:
        font = ImageFont.load_default(size=20)       # Pillow >= 10.1
    except TypeError:
        font = ImageFont.load_default()
    for i, (img, label) in enumerate([(original, "Original"), (ela_image, "ELA (brightened)"),
                                      (heat, "Heatmap (yellow = more change)")]):
        out.paste(img, (i * w, caption))
        draw.text((i * w + 8, 8), label, fill="black", font=font)
    return out


def analyse_to_png(
        image_bytes: bytes,
        quality: int = DEFAULT_QUALITY,
        block: int = DEFAULT_BLOCK) -> bytes:
    """Convenience for the API: the 3-panel picture as PNG bytes."""
    _, original, ela_image, heat = analyse(image_bytes, quality, block)
    buffer = io.BytesIO()
    panel(original, ela_image, heat).save(buffer, format="PNG")
    return buffer.getvalue()
