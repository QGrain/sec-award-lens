export type Provider = "google_scholar" | "openalex" | "semantic_scholar";

export interface Conference {
  id: string;
  name: string;
  short_name: string;
  organizer: string;
  aliases: string[];
}

export interface Author { name: string }
export interface InstitutionRef { display_name: string; openalex_id: string; ror?: string }
export interface AuthorEnrichment {
  author_name: string;
  openalex_author_id?: string;
  name_similarity: number;
  affiliations: InstitutionRef[];
}
export interface PaperEnrichment {
  paper_id: string;
  provider: "openalex";
  external_id: string;
  retrieved_at: string;
  primary_topic?: { display_name: string; openalex_id: string; score: number };
  authors: AuthorEnrichment[];
}
export interface Identifier {
  scheme: "doi" | "openalex" | "semantic_scholar" | "google_scholar" | "corpus_id";
  value: string;
  source_url: string;
  verified_at: string;
}

export interface Paper {
  id: string;
  canonical_title: string;
  authors: Author[];
  publication_year: number;
  venue_name: string;
  official_paper_url: string | null;
  identifiers: Identifier[];
  metadata_sources: string[];
}

export interface Award {
  id: string;
  edition_id: string;
  paper_id: string;
  raw_award_name: string;
  normalized_category: string;
  official_source: {
    url: string;
    retrieved_at: string;
    content_sha256: string;
    parser_version: string;
  };
  raw_title: string;
  raw_authors: string;
}

export interface CitationYear { year: number; count: number }
export interface Citation {
  paper_id: string;
  provider: Provider;
  external_id: string;
  retrieved_at: string;
  total_citations: number;
  citations_by_citing_year: CitationYear[];
  citations_first_3_years?: number | null;
}

export interface RankingRow {
  award: Award;
  paper: Paper;
  primary_topic: PaperEnrichment["primary_topic"] | null;
  /** Backward compatibility for locally cached JSON generated before schema v1.1. */
  enrichment?: PaperEnrichment | null;
  conference: Conference;
  citations: Partial<Record<Provider, Citation>>;
}

export interface Distribution {
  n: number;
  median?: number;
  mean?: number;
  q1?: number;
  q3?: number;
  min?: number;
  max?: number;
}

export interface ConferenceSummary {
  conference: Conference;
  award_count: number;
  cited_paper_count: number;
  citation_source?: Provider;
  citations: Distribution;
}

export interface YearData {
  schema_version: number;
  generated_at: string;
  year: number;
  rows: RankingRow[];
  conference_summaries: ConferenceSummary[];
}

export interface IndexData {
  schema_version: number;
  generated_at: string;
  years: number[];
  default_year: number;
  conferences: Conference[];
  citation_sources: Provider[];
  preferred_citation_source: Provider;
}

export interface Binding {
  paper_id: string;
  provider: Provider;
  external_id?: string;
  status: string;
  method?: string;
  confidence?: number | null;
  related_version_ids: string[];
  review_notes?: string;
}

export interface PaperData {
  generated_at: string;
  paper: Paper;
  enrichment: PaperEnrichment | null;
  awards: Award[];
  bindings: Binding[];
  citation_history: Partial<Record<Provider, Citation[]>>;
}
