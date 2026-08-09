from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class AwardCategory(StrEnum):
    BEST_PAPER = "best_paper"
    DISTINGUISHED_PAPER = "distinguished_paper"


class CitationProvider(StrEnum):
    OPENALEX = "openalex"
    SEMANTIC_SCHOLAR = "semantic_scholar"
    GOOGLE_SCHOLAR = "google_scholar"


class CitationRetrievalService(StrEnum):
    OPENALEX = "openalex"
    SEMANTIC_SCHOLAR = "semantic_scholar"
    SERPAPI = "serpapi"
    SCRAPERAPI = "scraperapi"


class BindingStatus(StrEnum):
    PENDING = "pending"
    CANDIDATE = "candidate"
    AUTO_VERIFIED = "auto_verified"
    MANUALLY_VERIFIED = "manually_verified"
    REJECTED = "rejected"
    STALE = "stale"


class MatchMethod(StrEnum):
    DOI_EXACT = "doi_exact"
    TITLE_EXACT = "title_exact"
    FUZZY_REVIEW = "fuzzy_review"
    MANUAL_OVERRIDE = "manual_override"


class SourceEvidence(StrictModel):
    url: str
    retrieved_at: datetime
    content_sha256: Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
    parser_version: str

    @field_validator("url")
    @classmethod
    def https_url(_cls, value: str) -> str:
        if not value.startswith("https://"):
            raise ValueError("provenance URLs must use HTTPS")
        return value

    @field_validator("retrieved_at")
    @classmethod
    def utc_timestamp(_cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
            raise ValueError("timestamps must be timezone-aware UTC")
        return value


class Conference(StrictModel):
    id: Annotated[str, Field(pattern=r"^[a-z0-9-]+$")]
    name: str
    short_name: str
    organizer: str
    aliases: list[str] = Field(default_factory=list)


class ConferenceEdition(StrictModel):
    id: Annotated[str, Field(pattern=r"^[a-z0-9-]+-\d{4}$")]
    conference_id: str
    year: Annotated[int, Field(ge=1980, le=2100)]
    official_event_url: str
    proceedings_url: str | None = None


class Author(StrictModel):
    name: str


class InstitutionRef(StrictModel):
    display_name: str
    openalex_id: Annotated[str, Field(pattern=r"^I\d+$")]
    ror: str | None = None


class AuthorEnrichment(StrictModel):
    author_name: str
    openalex_author_id: Annotated[str | None, Field(default=None, pattern=r"^A\d+$")]
    name_similarity: Annotated[float, Field(ge=0, le=1)]
    affiliations: list[InstitutionRef] = Field(default_factory=list)


class TopicAssignment(StrictModel):
    display_name: str
    openalex_id: Annotated[str, Field(pattern=r"^T\d+$")]
    score: Annotated[float, Field(ge=0, le=1)]


class Identifier(StrictModel):
    scheme: Literal[
        "doi", "openalex", "semantic_scholar", "google_scholar", "corpus_id"
    ]
    value: str
    source_url: str
    verified_at: datetime


class Paper(StrictModel):
    id: Annotated[str, Field(pattern=r"^[a-z0-9-]+$")]
    canonical_title: str
    authors: list[Author]
    publication_year: Annotated[int, Field(ge=1980, le=2100)]
    venue_name: str
    official_paper_url: str | None = None
    identifiers: list[Identifier] = Field(default_factory=list)
    metadata_sources: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_authors(self) -> Paper:
        if not self.authors:
            raise ValueError("paper must have at least one author")
        return self


class PaperEnrichment(StrictModel):
    """Reviewable provider metadata kept separate from canonical paper identity."""

    paper_id: str
    provider: Literal["openalex"]
    external_id: Annotated[str, Field(pattern=r"^W\d+$")]
    retrieved_at: datetime
    primary_topic: TopicAssignment | None = None
    authors: list[AuthorEnrichment] = Field(default_factory=list)

    @field_validator("retrieved_at")
    @classmethod
    def utc_timestamp(_cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
            raise ValueError("timestamps must be timezone-aware UTC")
        return value


class AwardGrant(StrictModel):
    id: Annotated[str, Field(pattern=r"^[a-z0-9-]+$")]
    edition_id: str
    paper_id: str
    raw_award_name: str
    normalized_category: AwardCategory
    official_source: SourceEvidence
    raw_title: str
    raw_authors: str


class CandidateEvidence(StrictModel):
    external_id: str
    title: str
    doi: str | None = None
    publication_year: int | None = None
    venue: str | None = None
    title_similarity: Annotated[float, Field(ge=0, le=1)]
    author_overlap: Annotated[float, Field(ge=0, le=1)]
    year_delta: int | None = None
    venue_match: bool = False


class ProviderBinding(StrictModel):
    paper_id: str
    provider: CitationProvider
    external_id: str | None = None
    status: BindingStatus
    method: MatchMethod | None = None
    confidence: Annotated[float | None, Field(default=None, ge=0, le=1)]
    selected_candidate: CandidateEvidence | None = None
    rejected_candidates: list[CandidateEvidence] = Field(default_factory=list)
    related_version_ids: list[str] = Field(default_factory=list)
    verified_by: str | None = None
    verified_at: datetime | None = None
    override_reason: str | None = None
    review_notes: str | None = None


class ManualOverride(StrictModel):
    paper_id: str
    provider: CitationProvider
    external_id: str
    reason: str
    verified_by: str
    verified_at: datetime
    evidence_urls: list[str] = Field(default_factory=list)


class ReviewMetadataPatch(StrictModel):
    canonical_title: str | None = None
    authors: list[str] | None = None
    publication_year: int | None = Field(default=None, ge=1980, le=2100)
    official_paper_url: str | None = None
    doi: str | None = None
    doi_source_url: str | None = None

    @model_validator(mode="after")
    def require_complete_doi_evidence(self) -> ReviewMetadataPatch:
        if bool(self.doi) != bool(self.doi_source_url):
            raise ValueError("doi and doi_source_url must be supplied together")
        if self.authors is not None and not self.authors:
            raise ValueError("authors must be omitted or contain at least one name")
        return self


class ReviewProviderDecision(StrictModel):
    provider: CitationProvider
    decision: Literal["verified", "ambiguous", "rejected", "not_found"]
    external_id: str | None = None
    candidate_url: str | None = None
    candidate_title: str | None = None
    candidate_authors: list[str] = Field(default_factory=list)
    candidate_publication_year: int | None = None
    candidate_venue: str | None = None
    candidate_doi: str | None = None
    related_version_ids: list[str] = Field(default_factory=list)
    confidence: Annotated[float | None, Field(default=None, ge=0, le=1)]
    reason: str
    evidence_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_verified_candidate(self) -> ReviewProviderDecision:
        if self.decision == "verified" and not all(
            (
                self.external_id,
                self.candidate_url,
                self.candidate_title,
                self.candidate_authors,
                self.candidate_publication_year,
                self.confidence,
                self.evidence_urls,
            )
        ):
            raise ValueError(
                "verified decisions require external_id, candidate_url, title, authors, "
                "publication year, confidence, and evidence_urls"
            )
        return self


class PaperResolutionSubmission(StrictModel):
    schema_version: Literal[1] = 1
    paper_id: str
    reviewer: str
    reviewed_at: datetime
    metadata: ReviewMetadataPatch = Field(default_factory=lambda: ReviewMetadataPatch())
    provider_decisions: list[ReviewProviderDecision] = Field(default_factory=list)
    evidence_urls: list[str] = Field(default_factory=list)
    notes: str | None = None

    @field_validator("reviewed_at")
    @classmethod
    def review_utc_timestamp(_cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
            raise ValueError("reviewed_at must be timezone-aware UTC")
        return value

    @model_validator(mode="after")
    def require_one_change(self) -> PaperResolutionSubmission:
        metadata_changes = any(
            value is not None for value in self.metadata.model_dump().values()
        )
        if not metadata_changes and not self.provider_decisions:
            raise ValueError("submission must contain metadata or a provider decision")
        providers = [decision.provider for decision in self.provider_decisions]
        if len(providers) != len(set(providers)):
            raise ValueError("submission contains duplicate provider decisions")
        return self


class CitationYearCount(StrictModel):
    year: Annotated[int, Field(ge=1800, le=2100)]
    count: Annotated[int, Field(ge=0)]


class CitationObservation(StrictModel):
    paper_id: str
    provider: CitationProvider
    external_id: str
    retrieved_at: datetime
    total_citations: Annotated[int, Field(ge=0)]
    influential_citations: Annotated[int | None, Field(default=None, ge=0)]
    citations_by_citing_year: list[CitationYearCount] = Field(default_factory=list)
    provider_record_updated_at: datetime | None = None
    retrieval_service: CitationRetrievalService | None = None
    response_sha256: Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
    request_fingerprint: str

    @field_validator("retrieved_at")
    @classmethod
    def observation_utc_timestamp(_cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
            raise ValueError("timestamps must be timezone-aware UTC")
        return value


class AwardCandidate(StrictModel):
    raw_title: str
    raw_authors: str
    authors: list[str]
    official_paper_url: str | None = None


class CoverageStatus(StrEnum):
    VERIFIED = "verified"
    PARTIAL = "partial"
    NO_CORE_AWARD_CONFIRMED = "no_core_award_confirmed"
    UNRESOLVED = "unresolved"


class CoverageEntry(StrictModel):
    edition_id: str
    status: CoverageStatus
    source_urls: list[str]
    notes: str | None = None


class AwardSourceRegistration(StrictModel):
    conference_id: str
    year: int
    url: str
    adapter: str
    expected_records: Annotated[int, Field(ge=0)]
    extracted_sha256: Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]


class CitationSourceRegistration(StrictModel):
    id: str
    role: str
    api_url: str
    public_output_enabled: bool
    stored_fields: list[str] = Field(default_factory=list)
    notes: str


class SourceRegistry(StrictModel):
    award_sources: list[AwardSourceRegistration]
    citation_sources: list[CitationSourceRegistration]


def utc_now() -> datetime:
    return datetime.now(UTC)
