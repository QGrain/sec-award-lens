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
from .providers.openalex import OpenAlexClient
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


@citations_app.command("refresh")
def refresh_citations(
    root: Annotated[Path | None, typer.Option()] = None,
    full_history: Annotated[
        bool, typer.Option(help="Query the citing-work graph by year.")
    ] = False,
    at: Annotated[
        str | None, typer.Option(help="UTC timestamp for a reproducible snapshot.")
    ] = None,
) -> None:
    """Refresh pinned, verified OpenAlex entities; never searches or rematches papers."""
    project = _root(root)
    bindings = [
        item
        for item in load_bindings(project)
        if item.provider == CitationProvider.OPENALEX
        and item.status in {BindingStatus.AUTO_VERIFIED, BindingStatus.MANUALLY_VERIFIED}
        and item.external_id
    ]
    paper_ids = {paper.id for paper in load_papers(project)}
    retrieved_at = datetime.fromisoformat(at.replace("Z", "+00:00")) if at else utc_now()
    with OpenAlexClient(api_key=_openalex_api_key()) as client:
        observations = [
            client.observation(
                paper_id=binding.paper_id,
                external_id=binding.external_id or "",
                full_history=full_history,
                retrieved_at=retrieved_at,
            )
            for binding in bindings
            if binding.paper_id in paper_ids
        ]
    date = retrieved_at.date().isoformat()
    target = project / "data/snapshots" / f"{date}-openalex.jsonl"
    if target.exists():
        raise typer.BadParameter(f"snapshot already exists: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(jsonl(observations), encoding="utf-8")
    typer.echo(f"wrote {len(observations)} observations to {target}")
