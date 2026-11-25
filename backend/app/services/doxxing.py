"""Pattern-based Doxxing detector (Section 6, brought forward from FYP-2).

Why patterns and not the model
  No source in dataset v1 has labelled Doxxing rows (taxonomy.yaml, open_decisions:
  doxxing_data), so the SVM cannot learn the class. Doxxing is, however, mostly visible
  as the identifiers themselves: a phone number, a CNIC, an e-mail address or a home
  address posted about someone. This module finds those with rules, and its result is
  reported next to the model's label, never as the label (docs/interfaces.md, section 1).

What it returns
  detect_doxxing(text) -> {"detected": bool, "match_types": [...]}

  match_types lists only the KINDS of identifier found, in the fixed order of
  MATCH_TYPES, without duplicates. The matched values are never returned, logged or
  stored, so no personal data is copied out of the evidence into results, custody
  payloads or logs. find_identifiers() gives types and character spans (still no values)
  for tests and a future reviewer highlight.

Identifier kinds (Pakistan-first, since that is where the evidence comes from)
  email          plain addresses, OCR spacing around "@", and spelled-out forms such as
                 "ali (at) gmail (dot) com"
  cnic           13-digit CNIC written 12345-1234567-1; a bare 13-digit run only when a
                 CNIC keyword (cnic, id card, shanakhti, شناختی ...) is nearby
  phone_number   Pakistani mobiles (03XX..., +92 3XX..., 923XX...), landlines
                 (0XX-XXXXXXX, +92 42 ...), and any "+"-prefixed international number
  address        one strong marker (house/flat/plot/makan followed by "no."/"number"/"#",
                 H# 12, مکان نمبر) or at least two different weaker components (house 12
                 without "no.", street/gali number, block, sector, phase,
                 mohalla/colony/housing society, an "address:" label)

  Urdu (۰-۹) and Arabic-Indic (٠-٩) digits are read as ASCII digits before matching.

Known limits (to be measured, not assumed)
  - It flags identifiers, not intent. A victim's own number in a chat header is flagged
    too. That is acceptable for an indicator that a human reviewer checks.
  - Addresses written without numbers or markers ("near the big mosque in Gulberg") are
    missed; a gazetteer or the language model is the FYP-2 route for those.
  - OCR letter/digit confusions (O for 0, l for 1) are not corrected.

Pure function: no I/O, no logging, no state.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

# Fixed order used in every result, so equal inputs give byte-identical JSON (custody hash).
MATCH_TYPES = ("phone_number", "cnic", "email", "address")

DETECTOR_VERSION = "patterns-v1"

# Urdu / Arabic-Indic digits -> ASCII. One character in, one out, so spans are preserved.
_DIGIT_MAP = str.maketrans(
    "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
    "01234567890123456789",
)

_SEP = r"[ \t.\-]?"          # one optional separator between digit groups
_NO_DIGIT_BEFORE = r"(?<![\d+])"
_NO_DIGIT_AFTER = r"(?![\d])"


# --------------------------------------------------------------------------- e-mail
_EMAIL_PLAIN = re.compile(
    r"(?<![\w.%+-])[A-Za-z0-9._%+-]{1,64}[ \t]?@[ \t]?[A-Za-z0-9-]{1,63}"
    r"(?:\.[A-Za-z0-9-]{1,63}){0,4}\.[A-Za-z]{2,24}(?![\w-])"
)
_TLD = r"(?:com|net|org|pk|edu|gov|co|io|info|me)\b"
_DOT = r"(?:\(dot\)|\[dot\]|\{dot\}|[ \t]dot[ \t]|\.)"
_EMAIL_SPELLED = (
    # Bracketed "at": ali (at) gmail (dot) com, ali[at]uni.edu.pk
    re.compile(
        r"(?<![\w.])[A-Za-z0-9._%+-]{1,64}[ \t]*(?:\(at\)|\[at\]|\{at\})[ \t]*"
        r"[A-Za-z0-9-]{1,63}(?:[ \t]*" + _DOT + r"[ \t]*[A-Za-z0-9-]{1,63}){0,3}?"
        r"[ \t]*" + _DOT + r"[ \t]*" + _TLD,
        re.IGNORECASE,
    ),
    # Bare word "at" is ordinary English, so it needs a spelled "dot" or a known
    # mail provider: "ali at gmail dot com", "ali at yahoo.com".
    re.compile(
        r"(?<![\w.])[A-Za-z0-9._%+-]{1,64}[ \t]+at[ \t]+(?:"
        r"[A-Za-z0-9-]{1,63}(?:[ \t]+dot[ \t]+[A-Za-z0-9-]{1,63}){0,3}?[ \t]+dot[ \t]+" + _TLD
        + r"|(?:gmail|googlemail|yahoo|hotmail|outlook|live|icloud|proton|protonmail)"
        r"[ \t]*" + _DOT + r"[ \t]*" + _TLD + r")",
        re.IGNORECASE,
    ),
)

# ----------------------------------------------------------------------------- CNIC
_CNIC_SEP = r"[ \t]?[-.][ \t]?|[ \t]"
_CNIC_FORMATTED = re.compile(
    _NO_DIGIT_BEFORE + r"[1-7]\d{4}(?:" + _CNIC_SEP + r")\d{7}(?:" + _CNIC_SEP + r")\d"
    + _NO_DIGIT_AFTER
)
_CNIC_BARE = re.compile(_NO_DIGIT_BEFORE + r"[1-7]\d{12}" + _NO_DIGIT_AFTER)
_CNIC_KEYWORD = re.compile(
    r"\b(?:c\.?n\.?i\.?c|n\.?i\.?c|id[ \t]?card|identity[ \t]card|shanakhti|shnakhti"
    r"|shanakhtee)\b|شناختی",
    re.IGNORECASE,
)
_CNIC_KEYWORD_WINDOW = 40  # characters either side of a bare 13-digit run

# ---------------------------------------------------------------------------- phone
_PHONE_PATTERNS = (
    # Pakistani mobile: 03XX-XXXXXXX, +92 3XX XXXXXXX, 0092-3XX-XXX-XXXX, 923XXXXXXXXX
    re.compile(
        _NO_DIGIT_BEFORE + r"(?:(?:\+|00)[ \t]?92|92|0)" + _SEP + r"\(?3\d{2}\)?" + _SEP
        + r"\d{3}" + _SEP + r"\d{4}" + _NO_DIGIT_AFTER
    ),
    # Pakistani landline: 042-35761234, (021) 3456 7890, +92 51 1234567
    re.compile(
        _NO_DIGIT_BEFORE + r"(?:(?:\+|00)[ \t]?92" + _SEP + r"|0)\(?[1-9]\d{1,3}\)?" + _SEP
        + r"\d{3,4}" + _SEP + r"\d{3,4}" + _NO_DIGIT_AFTER
    ),
    # Any "+"-prefixed international number with 8 to 15 digits.
    re.compile(r"(?<![\w+])\+\d(?:" + _SEP + r"\(?\d\)?){7,14}" + _NO_DIGIT_AFTER),
)

# -------------------------------------------------------------------------- address
_NUM = r"\d{1,5}[A-Za-z]?(?:[/-]\d{1,4}[A-Za-z]?)?"
_NO_WORD = r"(?:no\.?|number|num|nmbr|nambar|#)"

_UNIT = r"(?:house|makan|makaan|ghar|flat|apartment|apt|plot|bungalow)"

# One of these alone is enough: a unit word WITH "no." / "number" / "#" before the number.
_ADDRESS_STRONG = (
    re.compile(
        r"\b" + _UNIT + r"[ \t]*" + _NO_WORD + r"[ \t]*[:.]?[ \t]*" + _NUM + r"\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bh[ \t]*(?:#|\.[ \t]*no\.?)[ \t]*" + _NUM + r"\b", re.IGNORECASE),
    re.compile(r"(?:مکان|فلیٹ|پلاٹ|گھر)[ \t]*نمبر[ \t]*:?[ \t]*\d{1,5}"),
)

# Two DIFFERENT kinds of these are needed.
_ADDRESS_WEAK = {
    # "House 12" without "no." is common in real addresses, but "his house 3 times" is
    # ordinary text, so on its own it only counts as one weak component.
    "unit": (
        re.compile(r"\b" + _UNIT + r"[ \t]*" + _NUM + r"\b", re.IGNORECASE),
    ),
    "street": (
        re.compile(
            r"\b(?:street|st|gali|galli|lane|road|rd)\.?[ \t]*(?:" + _NO_WORD + r")?"
            r"[ \t]*[:#]?[ \t]*\d{1,4}\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b\d{1,4}(?:st|nd|rd|th)?[ \t]+(?:street|lane|road|avenue)\b", re.IGNORECASE
        ),
        re.compile(r"(?:گلی|سڑک|روڈ)[ \t]*(?:نمبر)?[ \t]*\d{1,4}"),
    ),
    "block": (
        # The block letter must be upper case, so "block a user" is not read as an address.
        re.compile(r"\b(?i:block|blk)\.?[ \t]*[-#:]?[ \t]*(?:[A-Z]{1,2}(?:-?\d{1,2})?|\d{1,3})\b"),
        re.compile(r"بلاک[ \t]*\S"),
    ),
    "sector": (
        re.compile(r"\b(?i:sector)[ \t]+[A-Z0-9]{1,2}(?:-?\d{1,2})?(?:/\d)?\b"),
        # Islamabad-style sector with sub-sector: G-9/2, F-7/3, I-8/4
        re.compile(r"\b[D-I]-?\d{1,2}/[1-4]\b"),
        re.compile(r"سیکٹر[ \t]*\S"),
    ),
    "phase": (
        re.compile(r"\b(?i:phase)[ \t]*[-#]?[ \t]*(?:\d{1,2}|[IVX]{1,4})\b"),
    ),
    "locality": (
        re.compile(
            r"\b(?:mohalla|mohallah|muhalla|muhallah|colony|housing[ \t]+society"
            r"|housing[ \t]+scheme|cooperative[ \t]+society)\b",
            re.IGNORECASE,
        ),
        re.compile(r"محلہ|محلے|کالونی|سوسائٹی"),
    ),
    "label": (
        # "address: ...", "pata: ..." but not "email address:" or "IP address:".
        re.compile(
            r"(?<!email )(?<!e-mail )(?<!ip )(?<!web )"
            r"\b(?:address|addr|pata|ghar[ \t]+ka[ \t]+pata)[ \t]*[:\-][ \t]*\S",
            re.IGNORECASE,
        ),
        re.compile(r"(?:پتہ|پتا)[ \t]*:"),
    ),
}


@dataclass(frozen=True)
class IdentifierMatch:
    """Where an identifier was found. Holds the kind and span only, never the value."""

    match_type: str
    start: int
    end: int


def _normalise(text: str) -> str:
    return text.translate(_DIGIT_MAP)


def _overlaps(start: int, end: int, taken: list) -> bool:
    return any(start < t_end and t_start < end for t_start, t_end in taken)


def _claim(pattern: re.Pattern, text: str, match_type: str, taken: list, out: list) -> None:
    """Add non-overlapping matches of one pattern, and mark their spans as taken."""
    for m in pattern.finditer(text):
        if not _overlaps(m.start(), m.end(), taken):
            taken.append((m.start(), m.end()))
            out.append(IdentifierMatch(match_type, m.start(), m.end()))


def _phone_digits_ok(span_text: str) -> bool:
    """National numbers with a leading 0 are 10-11 digits; others 8-15."""
    digits = re.sub(r"\D", "", span_text)
    if span_text.lstrip("( ").startswith("0") and not span_text.startswith("00"):
        return 10 <= len(digits) <= 11
    return 8 <= len(digits) <= 15


def _find_address(text: str) -> list:
    found = []
    for pattern in _ADDRESS_STRONG:
        found.extend(
            IdentifierMatch("address", m.start(), m.end()) for m in pattern.finditer(text)
        )
    if found:
        return found

    weak_hits = {}
    for kind, patterns in _ADDRESS_WEAK.items():
        for pattern in patterns:
            m = pattern.search(text)
            if m:
                weak_hits[kind] = IdentifierMatch("address", m.start(), m.end())
                break
    if len(weak_hits) >= 2:
        return sorted(weak_hits.values(), key=lambda x: x.start)
    return []


def find_identifiers(text: Optional[str]) -> list:
    """Return every identifier found, as IdentifierMatch objects ordered by position.

    Spans index into the text that was passed in. Matching order is e-mail, CNIC, phone,
    so that the digits of a CNIC or of an e-mail's local part are not reported a second
    time as a phone number. Address markers may overlap other kinds (a house number is
    also a number), so they are matched independently.
    """
    if text is None:
        return []
    if not isinstance(text, str):
        raise TypeError("text must be a str or None")
    if not text.strip():
        return []

    norm = _normalise(text)
    taken: list = []
    out: list = []

    _claim(_EMAIL_PLAIN, norm, "email", taken, out)
    for pattern in _EMAIL_SPELLED:
        _claim(pattern, norm, "email", taken, out)

    _claim(_CNIC_FORMATTED, norm, "cnic", taken, out)
    for m in _CNIC_BARE.finditer(norm):
        if _overlaps(m.start(), m.end(), taken):
            continue
        lo = max(0, m.start() - _CNIC_KEYWORD_WINDOW)
        hi = min(len(norm), m.end() + _CNIC_KEYWORD_WINDOW)
        if _CNIC_KEYWORD.search(norm, lo, hi):
            taken.append((m.start(), m.end()))
            out.append(IdentifierMatch("cnic", m.start(), m.end()))

    for pattern in _PHONE_PATTERNS:
        for m in pattern.finditer(norm):
            if _overlaps(m.start(), m.end(), taken):
                continue
            if _phone_digits_ok(m.group()):
                taken.append((m.start(), m.end()))
                out.append(IdentifierMatch("phone_number", m.start(), m.end()))

    out.extend(_find_address(norm))
    return sorted(out, key=lambda x: (x.start, x.end, x.match_type))


def detect_doxxing(text: Optional[str]) -> dict:
    """Doxxing indicator in the shape of docs/interfaces.md, section 1 (`doxxing` field).

    Returns {"detected": bool, "match_types": [...]} with match_types in MATCH_TYPES
    order. Empty or None text gives {"detected": False, "match_types": []}.
    """
    kinds = {m.match_type for m in find_identifiers(text)}
    match_types = [t for t in MATCH_TYPES if t in kinds]
    return {"detected": bool(match_types), "match_types": match_types}
