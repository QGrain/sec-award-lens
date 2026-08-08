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

Deployment of committed data needs no API key. Weekly OpenAlex refreshes and local
entity searches do.

1. Obtain the OpenAlex key from <https://openalex.org/settings/api>.
2. For local API commands, export it only in the current shell:

   ```bash
   export OPENALEX_API_KEY='your-key'
   ```

3. On GitHub, open **Settings → Secrets and variables → Actions → Secrets → New
   repository secret**.
4. Name it exactly `OPENALEX_API_KEY`, paste the key as its value, and save it.

Do not create `SEMANTIC_SCHOLAR_API_KEY` yet. Add it only after AI2 has answered the
public-snapshot/licensing question and S2 public output is deliberately enabled. Never
store either key in a repository variable: variables are not secrets.

## What each workflow does

| Workflow | Trigger | Expected result |
| --- | --- | --- |
| `CI` | Push to `main`; pull request | Python lint/type/tests, data/schema reproducibility checks, frontend tests/audit/build |
| `Deploy GitHub Pages` | Push to `main`; manual dispatch | Rebuild `web/public/data`, build `web/dist`, upload and deploy a Pages artifact |
| `Refresh citation snapshots` | Monday 08:17 UTC; manual dispatch | Fetch pinned OpenAlex IDs, append a dated snapshot, validate/build, and open a PR |
| `Monitor official award sources` | First day of each month at 09:43 UTC; manual dispatch | Compare normalized official award records with their reviewed count and digest |

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
4. Confirm that the footer shows the current OpenAlex retrieval date and that the
   GitHub link targets the actual repository.
5. Use a private browser window or disable cache once to ensure the result is the
   deployed artifact rather than a local Vite page.

## Verify automated updates

After adding `OPENALEX_API_KEY`, manually run **Actions → Refresh citation snapshots →
Run workflow** once instead of waiting for Monday. The expected result is a PR from
`automation/citation-refresh` containing:

- one new `data/snapshots/YYYY-MM-DD-openalex.jsonl` file;
- regenerated `web/public/data` files whose counts or timestamps changed;
- no binding search, rematch, or unrelated source edits.

The workflow validates the data before opening the PR. GitHub may show the PR's `CI`
run as **approval required** because the PR was created with `GITHUB_TOKEN`; approve
that run, wait for CI, inspect the diff, and merge manually. Merging to `main` triggers
a new Pages deployment. A second refresh on the same UTC date should report that the
snapshot already exists and should not create duplicate history.

Also manually run **Monitor official award sources** once. Success means all four
normalized 2023 official-source digests still match; failure requires human inspection
and must not automatically rewrite curated awards.

## Recommended repository protection

After the first successful deployment, add a `main` branch ruleset that requires pull
requests and the `validate` CI job before merge. Do not grant the refresh workflow
automatic merge rights. Keep the Pages `github-pages` environment managed by the
deployment workflow, and review dependency/action updates before changing pinned SHAs.

Common failures:

| Symptom | Check |
| --- | --- |
| Pages job cannot configure the site | Pages source is set to **GitHub Actions** |
| Refresh reports a missing key | Repository secret is named exactly `OPENALEX_API_KEY` |
| Refresh cannot open a PR | The workflow's write permissions and “Allow GitHub Actions to create and approve pull requests” are enabled |
| Site HTML loads but data is 404 | Vite was built in Actions with the repository subpath; inspect the deployed asset/data URLs |
| Automated PR has no running CI | Open the PR and approve its workflow run |
| Weekly/monthly jobs stopped | Re-enable schedules after prolonged repository inactivity |
