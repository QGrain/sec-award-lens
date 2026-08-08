from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any, TypeVar

import yaml
from pydantic import BaseModel

from .models import (
    AwardGrant,
    CitationObservation,
    Conference,
    ConferenceEdition,
    CoverageEntry,
    ManualOverride,
    Paper,
    PaperEnrichment,
    ProviderBinding,
    SourceRegistry,
)

T = TypeVar("T", bound=BaseModel)


def repository_root(start: Path | None = None) -> Path:
    candidate = (start or Path.cwd()).resolve()
    for path in (candidate, *candidate.parents):
        if (path / "pyproject.toml").exists():
            return path
    raise FileNotFoundError("could not locate repository root")


def read_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_model_list(path: Path, key: str, model: type[T]) -> list[T]:
    payload = read_yaml(path) or {}
    return [model.model_validate(item) for item in payload.get(key, [])]


def load_conferences(root: Path) -> list[Conference]:
    return load_model_list(root / "data/curated/conferences.yml", "conferences", Conference)


def load_editions(root: Path) -> list[ConferenceEdition]:
    return load_model_list(root / "data/curated/editions.yml", "editions", ConferenceEdition)


def load_papers(root: Path) -> list[Paper]:
    return load_model_list(root / "data/curated/papers.yml", "papers", Paper)


def load_enrichments(root: Path) -> list[PaperEnrichment]:
    return load_model_list(
        root / "data/curated/paper_enrichments.yml", "enrichments", PaperEnrichment
    )


def load_bindings(root: Path) -> list[ProviderBinding]:
    return load_model_list(root / "data/curated/bindings.yml", "bindings", ProviderBinding)


def load_coverage(root: Path) -> list[CoverageEntry]:
    return load_model_list(root / "data/provenance/coverage_matrix.yml", "coverage", CoverageEntry)


def load_overrides(root: Path) -> list[ManualOverride]:
    return load_model_list(
        root / "data/curated/manual_overrides.yml", "overrides", ManualOverride
    )


def load_source_registry(root: Path) -> SourceRegistry:
    return SourceRegistry.model_validate(
        read_yaml(root / "data/provenance/source_registry.yml")
    )


def load_awards(root: Path) -> list[AwardGrant]:
    awards: list[AwardGrant] = []
    for path in sorted((root / "data/curated/awards").glob("*/*.yml")):
        awards.extend(load_model_list(path, "awards", AwardGrant))
    return awards


def load_observations(root: Path) -> list[CitationObservation]:
    observations: list[CitationObservation] = []
    for path in sorted((root / "data/snapshots").glob("*.jsonl")):
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    observations.append(CitationObservation.model_validate_json(line))
    return observations


def stable_json(payload: Any, *, indent: int | None = 2) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=indent) + "\n"


def jsonl(models: Iterable[BaseModel]) -> str:
    return "".join(
        model.model_dump_json(exclude_none=True, by_alias=True) + "\n"
        for model in sorted(models, key=lambda item: repr(item.model_dump()))
    )
