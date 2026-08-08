from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Annotated

import typer

from .awards.sources import ADAPTERS, fetch_award_candidates
from .build import build_site_data, export_json_schemas
from .io import (
    jsonl,
    load_awards,
    load_bindings,
    load_editions,
    load_papers,
    load_source_registry,
    repository_root,
)
from .matching import resolve_candidates
from .models import BindingStatus, CitationProvider, utc_now
from .normalization import title_similarity
from .providers.google_scholar import GoogleScholarClient
from .providers.openalex import OpenAlexClient
from .providers.semantic_scholar import SemanticScholarClient
from .review import apply_resolution, load_submission
from .validation import validate_repository

app = typer.Typer(no_args_is_help=True, help="Build and verify the SecAwardLens dataset.")
awards_app = typer.Typer(no_args_is_help=True)
data_app = typer.Typer(no_args_is_help=True)
citations_app = typer.Typer(no_args_is_help=True)
schema_app = typer.Typer(no_args_is_help=True)
match_app = typer.Typer(no_args_is_help=True)
review_app = typer.Typer(no_args_is_help=True)
app.add_typer(awards_app, name="awards")
app.add_typer(data_app, name="data")
app.add_typer(citations_app, name="citations")
app.add_typer(schema_app, name="schema")
app.add_typer(match_app, name="match")
app.add_typer(review_app, name="review")


def _root(path: Path | None) -> Path:
    return path.resolve() if path else repository_root()


def _openalex_api_key() -> str:
    key = os.getenv("OPENALEX_API_KEY")
    if not key:
        raise typer.BadParameter(
            "OPENALEX_API_KEY is required. Create a free key at "
            "https://openalex.org/settings/api and export it or add it as a GitHub secret."
        )
    return key


def _semantic_scholar_api_key() -> str:
    key = os.getenv("S2_API_KEY")
    if not key:
        raise typer.BadParameter(
            "S2_API_KEY is required. Store the approved Semantic Scholar key in this "
            "environment or as a GitHub Actions repository secret."
        )
    return key


def _serpapi_key() -> str:
    key = os.getenv("SERPAPI_KEY")
    if not key:
        raise typer.BadParameter(
            "SERPAPI_KEY is required for Google Scholar via SerpApi. Create a key at "
            "https://serpapi.com/manage-api-key and export it or add it as a GitHub secret."
        )
    return key


@awards_app.command("check")
def check_awards(
    conference: Annotated[str | None, typer.Option()] = None,
    year: Annotated[int, typer.Option()] = 2023,
    root: Annotated[Path | None, typer.Option()] = None,
) -> None:
    """Parse official pages and print record counts without changing curated data."""
    project = _root(root)
    registry = load_source_registry(project)
    expected = {
        (item.conference_id, item.year): item.expected_records
        for item in registry.award_sources
    }
    keys = [key for key in ADAPTERS if key[1] == year and (not conference or key[0] == conference)]
    failed = False
    curated = load_awards(project)
    for conference_id, edition_year in keys:
        candidates, digest = fetch_award_candidates(conference_id, edition_year)
        actual = len(candidates)
        wanted = expected.get((conference_id, edition_year))
        stored_digests = {
            item.official_source.content_sha256
            for item in curated
            if item.edition_id == f"{conference_id}-{edition_year}"
        }
        typer.echo(f"{conference_id}-{edition_year}: {actual} papers; sha256={digest}")
        if wanted is not None and actual != wanted:
            failed = True
            typer.echo(f"  ERROR expected {wanted}", err=True)
        if stored_digests and digest not in stored_digests:
            failed = True
            typer.echo("  ERROR extracted records changed; review before updating digest", err=True)
    if failed:
        raise typer.Exit(1)


@data_app.command("validate")
def validate_data(root: Annotated[Path | None, typer.Option()] = None) -> None:
    report = validate_repository(_root(root))
    for warning in report.warnings:
        typer.echo(f"warning: {warning}", err=True)
    for error in report.errors:
        typer.echo(f"error: {error}", err=True)
    if not report.valid:
        raise typer.Exit(1)
    typer.echo("dataset is valid")


@app.command("build")
def build(root: Annotated[Path | None, typer.Option()] = None) -> None:
    written = build_site_data(_root(root))
    typer.echo(f"wrote {len(written)} static data files")


@schema_app.command("export")
def schema_export(root: Annotated[Path | None, typer.Option()] = None) -> None:
    written = export_json_schemas(_root(root))
    typer.echo(f"wrote {len(written)} schemas")


@review_app.command("validate")
def validate_review(
    form: Annotated[Path, typer.Argument(help="A paper-resolution YAML form.")],
) -> None:
    """Validate a structured human-review form without changing repository data."""
    submission = load_submission(form)
    typer.echo(f"valid review form for {submission.paper_id}")


@review_app.command("apply")
def apply_review(
    form: Annotated[Path, typer.Argument(help="A paper-resolution YAML form.")],
    root: Annotated[Path | None, typer.Option()] = None,
    write: Annotated[
        bool,
        typer.Option("--write", help="Write validated changes and rebuild site JSON."),
    ] = False,
) -> None:
    """Compile one review form into paper/binding/override records; dry-run by default."""
    project = _root(root)
    submission = load_submission(form)
    diff = apply_resolution(project, submission, write=write)
    if diff:
        typer.echo(diff)
        typer.echo("applied review and rebuilt site data" if write else "dry run only; add --write")
    else:
        typer.echo("review produces no data changes")


@match_app.command("openalex")
def match_openalex(
    root: Annotated[Path | None, typer.Option()] = None,
    paper_id: Annotated[
        str | None, typer.Option(help="Limit candidate generation to one paper.")
    ] = None,
) -> None:
    """Generate reviewable OpenAlex candidates without changing pinned bindings."""
    project = _root(root)
    papers = [paper for paper in load_papers(project) if not paper_id or paper.id == paper_id]
    awards = load_awards(project)
    editions = {item.id: item for item in load_editions(project)}
    conference_by_paper = {
        award.paper_id: editions[award.edition_id].conference_id for award in awards
    }
    decisions = []
    with OpenAlexClient(api_key=_openalex_api_key()) as client:
        for paper in papers:
            candidates = client.autocomplete_title(paper.canonical_title)
            plausible = [
                item
                for item in candidates
                if title_similarity(paper.canonical_title, item.title) >= 0.65
            ]
            decision = resolve_candidates(
                paper=paper,
                conference_id=conference_by_paper[paper.id],
                provider=CitationProvider.OPENALEX,
                candidates=plausible,
            )
            decisions.append(decision.model_dump(mode="json", exclude_none=True))
    typer.echo(json.dumps(decisions, ensure_ascii=False, indent=2, sort_keys=True))


@match_app.command("semantic-scholar")
def match_semantic_scholar(
    root: Annotated[Path | None, typer.Option()] = None,
    paper_id: Annotated[
        str | None, typer.Option(help="Limit candidate generation to one paper.")
    ] = None,
    all_papers: Annotated[
        bool,
        typer.Option("--all", help="Search every paper, not only unresolved OpenAlex papers."),
    ] = False,
) -> None:
    """Generate reviewable S2 candidates; never writes IDs or provider data."""
    project = _root(root)
    papers = load_papers(project)
    bindings = load_bindings(project)
    if paper_id:
        papers = [paper for paper in papers if paper.id == paper_id]
        if not papers:
            raise typer.BadParameter(f"unknown paper_id: {paper_id}")
    elif not all_papers:
        resolved_openalex = {
            item.paper_id
            for item in bindings
            if item.provider == CitationProvider.OPENALEX
            and item.status in {BindingStatus.AUTO_VERIFIED, BindingStatus.MANUALLY_VERIFIED}
        }
        papers = [paper for paper in papers if paper.id not in resolved_openalex]

    awards = load_awards(project)
    editions = {item.id: item for item in load_editions(project)}
    conference_by_paper = {
        award.paper_id: editions[award.edition_id].conference_id for award in awards
    }
    decisions = []
    with SemanticScholarClient(api_key=_semantic_scholar_api_key()) as client:
        for paper in papers:
            exact = client.title_candidate(paper.canonical_title)
            found = ([exact] if exact else []) + client.search_title(paper.canonical_title)
            candidates = list({item.external_id: item for item in found}.values())
            plausible = [
                item
                for item in candidates
                if item is not None
                and title_similarity(paper.canonical_title, item.title) >= 0.55
            ]
            decision = resolve_candidates(
                paper=paper,
                conference_id=conference_by_paper[paper.id],
                provider=CitationProvider.SEMANTIC_SCHOLAR,
                candidates=plausible,
            )
            decisions.append(decision.model_dump(mode="json", exclude_none=True))
    typer.echo(json.dumps(decisions, ensure_ascii=False, indent=2, sort_keys=True))


@match_app.command("google-scholar")
def match_google_scholar(
    root: Annotated[Path | None, typer.Option()] = None,
    paper_id: Annotated[
        str | None, typer.Option(help="Limit candidate generation to one paper.")
    ] = None,
) -> None:
    """Generate reviewable Scholar candidates through SerpApi; never pins IDs."""
    project = _root(root)
    papers = load_papers(project)
    if paper_id:
        papers = [paper for paper in papers if paper.id == paper_id]
        if not papers:
            raise typer.BadParameter(f"unknown paper_id: {paper_id}")
    awards = load_awards(project)
    editions = {item.id: item for item in load_editions(project)}
    conference_by_paper = {
        award.paper_id: editions[award.edition_id].conference_id for award in awards
    }
    decisions = []
    with GoogleScholarClient(api_key=_serpapi_key()) as client:
        for paper in papers:
            found, payload = client.search_title_with_payload(paper.canonical_title)
            plausible = [
                item
                for item in found
                if title_similarity(paper.canonical_title, item.title) >= 0.65
            ]
            decision = resolve_candidates(
                paper=paper,
                conference_id=conference_by_paper[paper.id],
                provider=CitationProvider.GOOGLE_SCHOLAR,
                candidates=plausible,
            )
            selected = next(
                (
                    item
                    for item in plausible
                    if item.external_id == decision.external_id
                ),
                None,
            )
            decisions.append(
                {
                    "paper_id": paper.id,
                    "expected": {
                        "title": paper.canonical_title,
                        "authors": [author.name for author in paper.authors],
                        "publication_year": paper.publication_year,
                        "venue": paper.venue_name,
                    },
                    "resolution": decision.model_dump(mode="json", exclude_none=True),
                    "initial_observation": (
                        client.discovery_observation(
                            paper_id=paper.id,
                            candidate=selected,
                            search_payload=payload,
                            query_title=paper.canonical_title,
                        ).model_dump(mode="json", exclude_none=True)
                        if selected is not None
                        else None
                    ),
                    "candidates": [
                        {
                            "cites_id": item.external_id,
                            "scholar_cluster_url": (
                                "https://scholar.google.com/scholar?cluster="
                                f"{item.external_id}"
                            ),
                            "title": item.title,
                            "authors": item.authors,
                            "publication_year": item.publication_year,
                            "publication_summary": item.venue,
                            "observed_citations_at_search": item.citation_count,
                            "result_url": item.raw.get("link"),
                        }
                        for item in plausible
                    ],
                }
            )
    typer.echo(json.dumps(decisions, ensure_ascii=False, indent=2, sort_keys=True))


@citations_app.command("refresh")
def refresh_citations(
    root: Annotated[Path | None, typer.Option()] = None,
    full_history: Annotated[
        bool, typer.Option(help="Query the citing-work graph by year.")
    ] = False,
    at: Annotated[
        str | None, typer.Option(help="UTC timestamp for a reproducible snapshot.")
    ] = None,
    provider: Annotated[
        str,
        typer.Option(
            help="Citation provider: openalex, semantic_scholar, google_scholar, or all."
        ),
    ] = "openalex",
    skip_existing: Annotated[
        bool,
        typer.Option(help="Skip a provider when its UTC-dated snapshot already exists."),
    ] = False,
) -> None:
    """Refresh pinned verified IDs directly; never searches or rematches papers."""
    project = _root(root)
    choices = {
        "openalex": [CitationProvider.OPENALEX],
        "semantic_scholar": [CitationProvider.SEMANTIC_SCHOLAR],
        "google_scholar": [CitationProvider.GOOGLE_SCHOLAR],
        "all": [
            CitationProvider.OPENALEX,
            CitationProvider.SEMANTIC_SCHOLAR,
            CitationProvider.GOOGLE_SCHOLAR,
        ],
    }
    if provider not in choices:
        raise typer.BadParameter(
            "provider must be openalex, semantic_scholar, google_scholar, or all"
        )
    public_sources = {
        item.id: item.public_output_enabled
        for item in load_source_registry(project).citation_sources
    }
    all_bindings = load_bindings(project)
    paper_ids = {paper.id for paper in load_papers(project)}
    retrieved_at = datetime.fromisoformat(at.replace("Z", "+00:00")) if at else utc_now()
    date = retrieved_at.date().isoformat()

    for selected in choices[provider]:
        if not public_sources.get(selected.value, False):
            typer.echo(f"skipped {selected.value}: public output is disabled")
            continue
        bindings = [
            item
            for item in all_bindings
            if item.provider == selected
            and item.status in {BindingStatus.AUTO_VERIFIED, BindingStatus.MANUALLY_VERIFIED}
            and item.external_id
            and item.paper_id in paper_ids
        ]
        if not bindings:
            typer.echo(f"skipped {selected.value}: no verified bindings")
            continue
        target = project / "data/snapshots" / f"{date}-{selected.value.replace('_', '-')}.jsonl"
        if target.exists():
            if skip_existing:
                typer.echo(f"skipped {selected.value}: snapshot already exists: {target}")
                continue
            raise typer.BadParameter(f"snapshot already exists: {target}")

        if selected == CitationProvider.OPENALEX:
            with OpenAlexClient(api_key=_openalex_api_key()) as client:
                observations = [
                    client.observation(
                        paper_id=binding.paper_id,
                        external_id=binding.external_id or "",
                        full_history=full_history,
                        retrieved_at=retrieved_at,
                    )
                    for binding in bindings
                ]
        elif selected == CitationProvider.SEMANTIC_SCHOLAR:
            with SemanticScholarClient(api_key=_semantic_scholar_api_key()) as client:
                observations = [
                    client.observation(
                        paper_id=binding.paper_id,
                        external_id=binding.external_id or "",
                        retrieved_at=retrieved_at,
                    )
                    for binding in bindings
                ]
        else:
            with GoogleScholarClient(api_key=_serpapi_key()) as client:
                observations = [
                    client.observation(
                        paper_id=binding.paper_id,
                        external_id=binding.external_id or "",
                        retrieved_at=retrieved_at,
                    )
                    for binding in bindings
                ]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(jsonl(observations), encoding="utf-8")
        typer.echo(f"wrote {len(observations)} observations to {target}")
