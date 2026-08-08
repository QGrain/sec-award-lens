from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag

from ..models import AwardCandidate
from ..normalization import split_author_names

PARSER_VERSION = "2023.1"


@dataclass(frozen=True)
class AwardPage:
    conference_id: str
    year: int
    url: str


ADAPTERS: dict[tuple[str, int], AwardPage] = {
    ("ieee-sp", 2023): AwardPage(
        "ieee-sp", 2023, "https://www.ieee-security.org/TC/SP2023/program-awards.html"
    ),
    ("usenix-security", 2023): AwardPage(
        "usenix-security",
        2023,
        "https://www.usenix.org/conference/usenixsecurity23/technical-sessions",
    ),
    ("acm-ccs", 2023): AwardPage(
        "acm-ccs", 2023, "https://www.sigsac.org/ccs/CCS_awards/ccs-bestpaper.html"
    ),
    ("ndss", 2023): AwardPage("ndss", 2023, "https://www.ndss-symposium.org/ndss2023/"),
}


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def parse_ieee_2023(html: str) -> list[AwardCandidate]:
    soup = BeautifulSoup(html, "html.parser")
    heading = soup.find(id="distinguished-paper-awards")
    if not isinstance(heading, Tag):
        raise ValueError("IEEE S&P award section not found")
    panel = heading.find_next_sibling("div")
    if not isinstance(panel, Tag):
        raise ValueError("IEEE S&P award panel not found")
    candidates: list[AwardCandidate] = []
    for item in panel.select(".list-group-item"):
        title_node = item.find("b")
        if not isinstance(title_node, Tag):
            continue
        title = normalize_space(title_node.get_text(" ", strip=True))
        title_node.extract()
        raw_authors = normalize_space(item.get_text(" ", strip=True))
        candidates.append(
            AwardCandidate(
                raw_title=title,
                raw_authors=raw_authors,
                authors=split_author_names(raw_authors),
            )
        )
    return candidates


def _usenix_author_names(authors_node: Tag) -> list[str]:
    fragments: list[str] = []
    for child in authors_node.children:
        if isinstance(child, NavigableString):
            fragments.append(str(child))
        elif isinstance(child, Tag) and child.name != "em":
            fragments.append(child.get_text(" "))
    return split_author_names(normalize_space(" ".join(fragments)))


def parse_usenix_2023(html: str) -> list[AwardCandidate]:
    soup = BeautifulSoup(html, "html.parser")
    candidates: list[AwardCandidate] = []
    for award in soup.find_all("p", string=re.compile("Distinguished Paper Award Winner")):
        article = award.find_parent("article")
        if not isinstance(article, Tag):
            continue
        title_link = article.select_one("h2 a")
        authors_node = article.select_one(".field-name-field-paper-people-text p")
        if not isinstance(title_link, Tag) or not isinstance(authors_node, Tag):
            continue
        raw_authors = normalize_space(authors_node.get_text(" ", strip=True))
        href = str(title_link.get("href", ""))
        paper_url = httpx.URL(ADAPTERS[("usenix-security", 2023)].url).join(href)
        candidates.append(
            AwardCandidate(
                raw_title=normalize_space(title_link.get_text(" ", strip=True)),
                raw_authors=raw_authors,
                authors=_usenix_author_names(authors_node),
                official_paper_url=str(paper_url),
            )
        )
    return candidates


def parse_ccs_2023(html: str) -> list[AwardCandidate]:
    soup = BeautifulSoup(html, "html.parser")
    year_heading = next(
        (
            heading
            for heading in soup.find_all("h3")
            if normalize_space(heading.get_text()) == "2023"
        ),
        None,
    )
    if not isinstance(year_heading, Tag):
        raise ValueError("CCS 2023 heading not found")
    awards_list = year_heading.find_next("ul")
    if not isinstance(awards_list, Tag):
        raise ValueError("CCS 2023 awards list not found")
    candidates: list[AwardCandidate] = []
    # The official page omits closing </li> tags, so HTML parsers represent the
    # records as nested list items. Read each item's direct children only.
    for item in awards_list.find_all("li"):
        author_node = item.find("b", recursive=False)
        if not isinstance(author_node, Tag):
            continue
        raw_authors = normalize_space(author_node.get_text(" ", strip=True))
        title_fragments: list[str] = []
        for child in item.children:
            if isinstance(child, Tag) and child.name == "li":
                break
            if isinstance(child, NavigableString):
                title_fragments.append(str(child))
        title = normalize_space(" ".join(title_fragments)).lstrip(", ")
        candidates.append(
            AwardCandidate(
                raw_title=title,
                raw_authors=raw_authors,
                authors=split_author_names(raw_authors),
            )
        )
    return candidates


def parse_ndss_2023(html: str) -> list[AwardCandidate]:
    soup = BeautifulSoup(html, "html.parser")
    heading = next(
        (
            node
            for node in soup.find_all(["h2", "h3"])
            if "Distinguished Paper Award Winners" in node.get_text(" ", strip=True)
        ),
        None,
    )
    if not isinstance(heading, Tag):
        raise ValueError("NDSS award section not found")
    candidates: list[AwardCandidate] = []
    node = heading.find_next_sibling()
    while isinstance(node, Tag) and node.name not in {"h2", "h3"}:
        if node.name == "p":
            link = node.find("a")
            strong = node.find("strong")
            if isinstance(link, Tag) and isinstance(strong, Tag):
                title = normalize_space(strong.get_text(" ", strip=True))
                strong.extract()
                raw_authors = normalize_space(node.get_text(" ", strip=True))
                candidates.append(
                    AwardCandidate(
                        raw_title=title,
                        raw_authors=raw_authors,
                        authors=split_author_names(raw_authors),
                        official_paper_url=str(link.get("href")),
                    )
                )
        node = node.find_next_sibling()
    return candidates


PARSERS = {
    ("ieee-sp", 2023): parse_ieee_2023,
    ("usenix-security", 2023): parse_usenix_2023,
    ("acm-ccs", 2023): parse_ccs_2023,
    ("ndss", 2023): parse_ndss_2023,
}


def fetch_award_candidates(
    conference_id: str, year: int, *, client: httpx.Client | None = None
) -> tuple[list[AwardCandidate], str]:
    key = (conference_id, year)
    page = ADAPTERS[key]
    owned_client = client is None
    active_client = client or httpx.Client(
        follow_redirects=True,
        timeout=45,
        headers={"User-Agent": "SecAwardLens/0.1 (+https://github.com/)"},
    )
    try:
        response = active_client.get(page.url)
        response.raise_for_status()
        candidates = PARSERS[key](response.text)
        # Hash the extracted award records, not navigation, analytics, or other
        # unrelated page markup that may change on every request.
        canonical = json.dumps(
            [candidate.model_dump(mode="json") for candidate in candidates],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        digest = hashlib.sha256(canonical).hexdigest()
        return candidates, digest
    finally:
        if owned_client:
            active_client.close()
