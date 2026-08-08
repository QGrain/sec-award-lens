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
`S2_API_KEY`. This enables the manual candidate-discovery Action immediately. It does
not publish S2 data while `semantic_scholar.public_output_enabled` remains false.
Never use `SEMANTIC_SCHOLAR_API_KEY` (the code does not read that name), and never store
either key in a repository variable: variables are not secrets.

## What each workflow does

| Workflow | Trigger | Expected result |
| --- | --- | --- |
| `CI` | Push to `main`; pull request | Python lint/type/tests, data/schema reproducibility checks, frontend tests/audit/build |
| `Deploy GitHub Pages` | Push to `main`; manual dispatch | Rebuild `web/public/data`, build `web/dist`, upload and deploy a Pages artifact |
| `Refresh citation snapshots` | First day of each month at 08:17 UTC; manual dispatch | Fetch pinned IDs from enabled providers, append dated snapshots, validate/build, and open a PR |
| `Monitor official award sources` | First day of each month at 09:43 UTC; manual dispatch | Compare normalized official award records with their reviewed count and digest |
| `Find Semantic Scholar candidates` | Manual dispatch | Search OpenAlex-unresolved records below 1 req/s and upload review-only candidate JSON |

The off-hour cron minutes reduce peak scheduling delays. Scheduled workflows run only
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
4. Confirm that the footer shows the current citation-data retrieval date and that the
   GitHub link targets the actual repository.
5. Use a private browser window or disable cache once to ensure the result is the
   deployed artifact rather than a local Vite page.

## Verify automated updates

After adding `OPENALEX_API_KEY`, manually run **Actions → Refresh citation snapshots →
Run workflow** once instead of waiting for the next month. The expected result is a PR from
`automation/citation-refresh` containing:

- one new `data/snapshots/YYYY-MM-DD-openalex.jsonl` file;
- regenerated `web/public/data` files whose counts or timestamps changed;
- no binding search, rematch, or unrelated source edits.

The workflow validates the data before opening the PR. GitHub may show the PR's `CI`
run as **approval required** because the PR was created with `GITHUB_TOKEN`; approve
that run, wait for CI, inspect the diff, and merge manually. Merging to `main` triggers
a new Pages deployment. A second refresh on the same UTC date should report that the
snapshot already exists and should not create duplicate history.

After adding `S2_API_KEY`, run **Actions → Find Semantic Scholar candidates → Run
workflow** with the paper ID blank. Download the `semantic-scholar-candidates` artifact
from the completed run; it contains candidates for the five OpenAlex-unresolved papers.
This Action never edits the repository. Transfer only manually verified decisions into
the review form described in `docs/manual-curation-workflow.md`.

To publish an accepted S2 entity after the static-redistribution question is confirmed:

1. Change `semantic_scholar.public_output_enabled` to `true` in
   `data/provenance/source_registry.yml` and update the data notice in the same PR.
2. Apply the reviewed resolution form so the S2 ID is pinned.
3. Merge after CI; then manually run **Refresh citation snapshots**. Its next PR will
   contain `YYYY-MM-DD-semantic-scholar.jsonl` and provider-labeled site JSON.
4. Inspect the S2 count and attribution, merge the PR, and let the normal `main` push
   deploy it. The current S2 adapter does not retrieve the same by-year series as
   OpenAlex, so its three-year metric remains unavailable rather than zero.

Also manually run **Monitor official award sources** once. Success means all four
normalized 2023 official-source digests still match; failure requires human inspection
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
| Refresh reports a missing key | Repository secret is named exactly `OPENALEX_API_KEY` |
| Refresh cannot open a PR | The workflow's write permissions and “Allow GitHub Actions to create and approve pull requests” are enabled |
| Site HTML loads but data is 404 | Vite was built in Actions with the repository subpath; inspect the deployed asset/data URLs |
| Automated PR has no running CI | Open the PR and approve its workflow run |
| Monthly jobs stopped | Re-enable schedules after prolonged repository inactivity |
