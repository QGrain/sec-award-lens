# Local development and GitHub deployment

## Local preview

From the repository root:

```bash
uv sync --all-extras
uv run secawardlens data validate
uv run secawardlens build
cd web
npm ci
npm run dev
```

Open <http://localhost:5173>. Re-run `secawardlens build` after changing curated data
or Python metric/build code. For a production-equivalent check:

```bash
cd web
npm run build
npm run preview
```

Open <http://localhost:4173>. Local preview uses committed files under
`web/public/data/` and does not call a scholarly API.

## Pre-push checklist

Run the same contract checks as CI:

```bash
uv run ruff check .
uv run mypy
uv run pytest
uv run secawardlens data validate
uv run secawardlens schema export
uv run secawardlens build
cd web
npm ci
npm test
npm audit --audit-level=moderate
npm run build
```

Before committing, inspect `git status --short`, confirm that no `.env`, credentials,
private keys, local databases, or build/cache directories are staged, then run
`git diff --cached --check`. Git commit metadata includes the configured Git name and
email; use a GitHub noreply email if that is the desired public identity.

## Repository and Actions settings

1. Create or open the GitHub repository and make `main` its default branch. For GitHub
   Free Pages hosting, keep this open-source repository public.
2. Open **Settings → Actions → General**. Under **Actions permissions**, enable the
   workflows and external actions used by this repository. The checked-in workflows
   pin every external action to a full commit SHA.
3. Under **Workflow permissions**, the restrictive default token setting can remain in
   place because each workflow declares its required permissions. Enable **Allow
   GitHub Actions to create and approve pull requests** so the citation-refresh job can
   open its review PR. The workflow creates PRs but does not auto-approve or merge them.
4. In **Settings → Pages**, select **GitHub Actions** under **Build and deployment →
   Source**. Do not select “Deploy from a branch.”
5. In **Settings → Security / Advanced Security**, confirm secret scanning for the
   public repository and enable push protection when the option is available.
6. Push the reviewed commit with `git push -u origin main`.

If a push occurs before the Pages source is selected and the run fails during Pages
configuration, finish step 4 and use **Actions → Deploy GitHub Pages → Run workflow**;
no code change is needed.

## Repository secrets

Deployment of committed data needs no API key. Monthly OpenAlex refreshes and local
entity searches do.

1. Obtain the OpenAlex key from <https://openalex.org/settings/api>.
2. For local API commands, export it only in the current shell:

   ```bash
   export OPENALEX_API_KEY='your-key'
   ```

3. On GitHub, open **Settings → Secrets and variables → Actions → Secrets → New
   repository secret**.
4. Name it exactly `OPENALEX_API_KEY`, paste the key as its value, and save it.

Repeat the secret steps for the approved Semantic Scholar key, naming it exactly
`S2_API_KEY`. This enables manual candidate discovery and refreshes verified, pinned
S2 paper IDs at less than one request per second.
Never use `SEMANTIC_SCHOLAR_API_KEY` (the code does not read that name), and never store
either key in a repository variable: variables are not secrets.

For Google Scholar observations, copy the private key from the SerpApi account page
and create a third repository secret named exactly `SERPAPI_KEY`. Locally, use
`export SERPAPI_KEY='...'`. The key is sent only to SerpApi as its documented
`api_key` parameter; it is excluded from request fingerprints and generated data.

Optionally create `SCRAPERAPI_KEY` from the ScraperAPI dashboard. Monthly refresh reads
both services' live remaining capacity, prefers SerpApi when it can cover the batch,
and falls back to ScraperAPI when necessary. Current Google SERP pricing is 25
ScraperAPI credits per paper, so the current 84 verified Scholar clusters need at
least 2,100 credits.
Do not add `ZENROWS_API_KEY` to GitHub Actions yet. The strongest documented Fetch
configuration can resolve individual Scholar pages, but batch tests still produced
CAPTCHA and concurrency/rate-limit failures. The production workflow intentionally
excludes it until a complete low-concurrency verification succeeds.

## Optional public traffic counter

The footer supports GoatCounter, an open-source, cookie-free traffic counter. It is
disabled when no site code is configured, so the repository builds without an
analytics account.

1. Create a GoatCounter site at <https://www.goatcounter.com/> and note its short site
   code (the `CODE` in `https://CODE.goatcounter.com`).
2. In GoatCounter **Settings**, enable **Allow adding visitor counts on your website**.
   This is off by default and is required for the footer's site-wide total.
3. In GitHub, open **Settings → Secrets and variables → Actions → Variables → New
   repository variable**. Name it `GOATCOUNTER_CODE` and enter only the short code.
   This is a public browser configuration value, not a secret.
4. Re-run **Deploy GitHub Pages**, or push a commit to `main`.

For local layout testing, set `VITE_GOATCOUNTER_CODE=CODE` in `web/.env.local` before
starting Vite. GoatCounter filters localhost by default, so previewing the footer does
not increment production traffic. The site uses the versioned `count.v5.js` script
with subresource integrity, records hash-route page views, and displays the cached
site-wide total. Ad blockers or a disabled public counter may leave the number as `—`;
analytics failure never blocks the application.

## What each workflow does

| Workflow | Trigger | Expected result |
| --- | --- | --- |
| `CI` | Push to `main`; pull request | Python lint/type/tests, data/schema reproducibility checks, frontend tests/audit/build |
| `Deploy GitHub Pages` | Push to `main`; manual dispatch | Rebuild `web/public/data`, build `web/dist`, upload and deploy a Pages artifact |
| `Refresh citation snapshots` | Tenth day of each month at 08:17 UTC; manual dispatch | Check Scholar transport capacity, fetch pinned IDs, append dated snapshots, validate/build, and open a PR |
| `Monitor official award sources` | First day of each month at 09:43 UTC; manual dispatch | Compare normalized official award records with their reviewed count and digest |

The citation refresh runs after the current SerpApi plan's eighth-day renewal, with a
two-day buffer for settlement and timezone differences. The off-hour cron minutes
reduce peak scheduling delays. Scheduled workflows run only
from the default branch and may be delayed. GitHub disables schedules in a public
repository after 60 days without repository activity; re-enable them from the Actions
tab if the project has been dormant.

## First deployment verification

1. In **Actions**, confirm that `CI` and `Deploy GitHub Pages` are green for the same
   commit SHA.
2. Open the deployment job's `environment_url`. For the expected owner/repository name,
   the URL is `https://qgrain.github.io/sec-award-lens/`.
3. Verify the overview, pagination, conference filters, comparison tabs, methodology,
   and at least one `#/paper/...` route. Confirm that data files load from the
   `/sec-award-lens/data/` subpath rather than the domain root.
4. Confirm that the footer shows the current citation-data retrieval date, the traffic
   total if configured, and that the GitHub link targets the actual repository.
5. Use a private browser window or disable cache once to ensure the result is the
   deployed artifact rather than a local Vite page.

## Verify automated updates

The reviewed 2021–2023 snapshots are already committed, so the next push and Pages deploy
do not require a manual refresh. On the next scheduled run, or when manually dispatching
**Actions → Refresh citation snapshots**, the expected result is a PR from
`automation/citation-refresh` containing:

- one new dated snapshot for each enabled provider with verified bindings;
- regenerated `web/public/data` files whose counts or timestamps changed;
- no binding search, rematch, or unrelated source edits.

The workflow validates the data before opening the PR. GitHub may show the PR's `CI`
run as **approval required** because the PR was created with `GITHUB_TOKEN`; approve
that run, wait for CI, inspect the diff, and merge manually. Merging to `main` triggers
a new Pages deployment. A second refresh on the same UTC date should report that the
snapshot already exists and should not create duplicate history.

Candidate discovery is intentionally local rather than a standing GitHub workflow.
When adding a new year or correcting an entity, run `secawardlens match
semantic-scholar --paper-id PAPER_ID` or `secawardlens match google-scholar --paper-id
PAPER_ID`, review the output, and submit the accepted binding through the structured
review form. This avoids accumulating downloadable third-party candidate artifacts in
Actions and makes quota use an explicit maintainer decision. Check SerpApi quota before
an all-paper discovery pass.

To publish a newly accepted S2 entity, apply the reviewed resolution form so its ID is
pinned, then run **Refresh citation snapshots**. Inspect the resulting
`YYYY-MM-DD-semantic-scholar.jsonl`, provider link, count, and attribution before
merging. The current S2 adapter does not retrieve the same by-year series as OpenAlex,
so its three-year metric remains unavailable rather than zero.

Also manually run **Monitor official award sources** once. Success means all twelve
normalized 2021–2023 official-source digests still match; failure requires human inspection
and must not automatically rewrite curated awards.

## Recommended repository protection

After the first successful deployment, add a `main` branch ruleset that requires pull
requests and the `validate` CI job before merge. Keep the Pages `github-pages`
environment managed by the deployment workflow, and review dependency/action updates
before changing pinned SHAs.

### Optional automated merge and branch cleanup

The current workflow intentionally opens a PR but does not merge it. This is recommended
while provider behavior is still being validated. Enable **Settings → General → Pull
Requests → Automatically delete head branches** for immediate cleanup after any merge.
The action's `delete-branch: true` is also a fallback when it next observes a merged or
no-diff automation branch.

GitHub's repository auto-merge setting does not automatically opt every new bot PR in;
a writer can click **Enable auto-merge** on each PR. Fully unattended opt-in requires a
GitHub App installation token or a carefully scoped fine-grained PAT plus an explicit
`gh pr merge --auto` step. A PR created or merged with the default `GITHUB_TOKEN` has
workflow-recursion restrictions, so CI and Pages may not trigger as expected. Do not
add a long-lived broad PAT merely for convenience.

If full automation is later enabled, require the `validate` check, restrict it to the
exact `automation/citation-refresh` branch and title, use squash merge, and retain a
manual workflow kill switch. The principal risk is that syntactically valid but
semantically wrong provider changes would be published without a human diff review.

Common failures:

| Symptom | Check |
| --- | --- |
| Pages job cannot configure the site | Pages source is set to **GitHub Actions** |
| Refresh reports a missing key | Secret name matches the selected provider: `OPENALEX_API_KEY`, `S2_API_KEY`, and at least one of `SERPAPI_KEY` / `SCRAPERAPI_KEY` |
| Refresh cannot open a PR | The workflow's write permissions and “Allow GitHub Actions to create and approve pull requests” are enabled |
| Site HTML loads but data is 404 | Vite was built in Actions with the repository subpath; inspect the deployed asset/data URLs |
| Automated PR has no running CI | Open the PR and approve its workflow run |
| Monthly jobs stopped | Re-enable schedules after prolonged repository inactivity |
