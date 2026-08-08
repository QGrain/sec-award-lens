from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from urllib.parse import unquote

from rapidfuzz.fuzz import ratio

_DOI_PREFIX = re.compile(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", re.I)
_TRAILING_DOI_PUNCTUATION = ".,;:)]}>"
_PARENS = re.compile(r"\s*\([^()]*\)")
_NON_WORD = re.compile(r"[^\w]+", re.UNICODE)
_SPACE = re.compile(r"\s+")


def normalize_doi(value: str) -> str:
    normalized = unquote(value.strip())
    normalized = _DOI_PREFIX.sub("", normalized)
    return normalized.rstrip(_TRAILING_DOI_PUNCTUATION).lower()


def normalize_title(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    value = value.replace("{", "").replace("}", "")
    value = value.replace("’", "'").replace("‘", "'")
    value = value.replace("–", "-").replace("—", "-")
    return _SPACE.sub(" ", _NON_WORD.sub(" ", value)).strip()


def slugify(value: str, *, max_length: int = 64) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value.casefold()).strip("-")
    return slug[:max_length].rstrip("-")


def strip_affiliations(raw: str) -> str:
    previous = raw
    while True:
        current = _PARENS.sub("", previous)
        if current == previous:
            break
        previous = current
    return _SPACE.sub(" ", previous).strip(" ,;")


def split_author_names(raw: str) -> list[str]:
    clean = strip_affiliations(raw)
    clean = re.sub(r"\s+(?:and|&)\s+", ", ", clean)
    names = [name.strip(" ,;") for name in re.split(r"[,;]", clean)]
    return [name for name in names if name]


def surname(name: str) -> str:
    parts = normalize_title(name).split()
    return parts[-1] if parts else ""


def author_overlap(expected: Iterable[str], candidate: Iterable[str]) -> float:
    left = {surname(name) for name in expected if surname(name)}
    right = {surname(name) for name in candidate if surname(name)}
    if not left or not right:
        return 0.0
    return len(left & right) / len(left)


def title_similarity(left: str, right: str) -> float:
    return ratio(normalize_title(left), normalize_title(right)) / 100.0

