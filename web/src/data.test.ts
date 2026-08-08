import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { compactNumber, formatDate } from "./data";
import type { YearData } from "./types";

describe("formatters", () => {
  it("formats small citation counts without compact notation", () => {
    expect(compactNumber(119)).toBe("119");
  });

  it("formats snapshot timestamps as a readable date", () => {
    expect(formatDate("2026-08-07T12:00:00Z")).toContain("2026");
  });
});

describe("generated 2023 contract", () => {
  const data = JSON.parse(
    readFileSync(join(process.cwd(), "public/data/years/2023.json"), "utf8"),
  ) as YearData;

  it("contains all official 2023 award records", () => {
    expect(data.schema_version).toBe(2);
    expect(data.rows).toHaveLength(47);
    expect(data.rows.filter((row) => row.citations.openalex)).toHaveLength(42);
  });

  it("reports paper denominators for every conference", () => {
    expect(data.conference_summaries.map((item) => item.award_count)).toEqual([12, 16, 17, 2]);
  });
});
