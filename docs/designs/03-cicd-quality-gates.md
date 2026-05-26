# Design Document: Adding Real CI/CD Quality Gates, Security Checks, and Preview Deployments to martyschneider.com

**Version:** 1.0  
**Date:** 2026-05-25  
**Author:** Systems Architect (Grok-assisted design for solo maintainer)  
**Status:** Draft — Ready for owner review and iteration  
**Repository:** https://github.com/marty-schneider/personal-website  
**Related Artifacts:**  
- Security & Hardening Case Study: `docs/designs/01-security-case-study.md` (and its summary)  
- Current NVD pipeline: `.github/workflows/update-nvd-feed.yml`  
- Hosting migration context and project bible: `claude.md`

---

## Overview

This document designs the addition of a production-grade, low-maintenance CI/CD pipeline featuring meaningful quality gates, security scanning, and preview deployment capabilities for the martyschneider.com personal portfolio repository.

The objective is to evolve the current implicit "push-to-main deploys" model into an explicit, auditable DevSecOps pipeline that:

- Blocks low-quality or risky changes before they reach production.
- Generates strong, referenceable evidence of engineering rigor that directly powers the "Security Case Study" living artifact on the site.
- Seamlessly supports and de-risks the planned migration from GitHub Pages + Cloudflare proxy to native Cloudflare Pages.
- Remains sustainable and low-toil for a solo maintainer.

The design leverages only free tiers: GitHub Actions (public repository), GitHub's native security features (CodeQL, Dependabot, secret scanning), carefully chosen high-signal open-source scanners, and Cloudflare Pages' first-class free preview deployments and GitHub integration.

Concrete deliverables include a new primary workflow (`.github/workflows/ci.yml`), supporting scripts and data artifacts (`data/pipeline-status.json`), new documentation (`README.md`, `SECURITY.md`), updates to the existing NVD workflow and site, and direct file/line citations usable by the security case study page.

---

## Background & Motivation

**Current state (2026-05-25 local checkout of `/home/marty/personal-website`):**

- **One workflow only**: `.github/workflows/update-nvd-feed.yml` (nightly cron at 12:15 UTC + `workflow_dispatch`; `permissions: { contents: write }`; runs `scripts/update_nvd_feed.py` which fetches recent CVEs from NVD API 2.0 using optional `NVD_API_KEY` secret and commits only `data/nvd-recent.json` via github-actions[bot]).
- **Deployment**: GitHub Pages serving the repository root (with empty `.nojekyll`). Cloudflare provides DNS + edge proxy (and currently some headers). A `_headers` file exists at root and is **explicitly prepared for Cloudflare Pages** (see comments and directives for HSTS, nosniff, DENY framing, Permissions-Policy, Referrer-Policy, and cache rules for `/img/*`, `/fonts/*`, `/data/*`).
- **Application**: Monolithic `index.html` (~103 kB with heavy inline CSS/JS for the "Sector 7, Neo-CI" cyberpunk terminal aesthetic, compass navigation, news ticker). Self-hosted fonts (31 WOFF2/WOFF files under `fonts/`). Separate `css/styles.css` and `js/main.js` exist but are **legacy and not loaded** by production `index.html`. No build step, no root `package.json`, no frameworks.
- **Private zero-trust subsystem**: `private-vault/` directory containing a minimal TypeScript Cloudflare Worker (`src/worker.ts`, `wrangler.toml` binding R2 bucket `private-vault` and route `learning.martyschneider.com/*`, `package.json` with `typecheck`, `deploy`, and R2 upload scripts, `tsconfig.json`). The worker implements strict `resolveKey` path-traversal protection, GET/HEAD only, and privacy headers (`Cache-Control: private, no-store`, `no-referrer`). Content lives only in R2; never in the public repo. Protected by Cloudflare Access (email OTP, owner-only policy).
- **Critical gaps**: Zero PR checks. No automated testing, linting, SAST, secret scanning, dependency review, or link validation. No preview environments. Direct pushes to `main` (or the NVD bot) become live. The NVD workflow itself uses unpinned actions and broad permissions.
- **Strong existing signals** (documented in the companion security design): Self-hosted everything (no external script origins or Google Fonts), prepared edge hardening in `_headers`, real gated Worker with anti-traversal logic at `private-vault/src/worker.ts:12-17`, and the NVD pipeline as a "security sensor" (client fetch in `index.html:2676` uses `cache: 'no-store'` with graceful fallback to curated `NEWS` array).

The companion **Security & Hardening Case Study design** (`docs/designs/01-security-case-study.md`) explicitly calls out the current implicit/scattered nature of the posture and lists concrete future improvements needed for credibility:

- Pinning GitHub Actions to commit SHAs (see also existing workflow at lines 15-17).
- Header-drift detection CI job using curl validation against expectations in `_headers`.
- Adding `SECURITY.md`.
- Automated validation of hardening controls as part of "Living Aspects & Update Process."

The mismatch is material: the portfolio markets deep expertise in "securing software in CI—SAST, SCA, secrets, IaC policy, containers, SBOM" (see `index.html` meta description, JSON-LD, and "PIPELINE SECURITY" section around line 2025), yet the repository that hosts this message itself has no such controls. Senior DevSecOps reviewers will notice.

The planned Cloudflare Pages migration is the ideal forcing function. Cloudflare Pages offers **native, zero-config preview deployments for every PR** (unique URLs, full application of `_headers`, instant visual + security header review). The CI design must make this migration both safer and more impressive.

---

## Goals & Non-Goals

### Goals

1. **Real, impressive gates** (not checkbox theater): Controls a senior DevSecOps engineer would respect and cite in interviews or reviews — workflow static analysis (zizmor), SAST with SARIF (CodeQL), secret scanning (gitleaks + GitHub), supply-chain hygiene (pinned actions + dependency review + osv-scanner), static site integrity (link checking via lychee, asset hygiene, header validation), and private component validation.
2. **First-class preview support aligned to migration**: Primary preview mechanism becomes Cloudflare Pages native previews. CI gates run in GitHub in parallel; previews are available immediately for human review.
3. **Solo-maintainer friendly**: Total new workflow YAML kept under ~160 lines; reuse existing Python and npm scripts; no new heavy frameworks or build tools for the site itself; fast local reproduction of most checks; failures provide clear, actionable output.
4. **Visible, multi-surface signals**:
   - GitHub PR checks matrix + branch protection status.
   - Badges in new root `README.md`.
   - "Last verified" timestamp + direct workflow run link surfaced in the existing terminal (`status` command) and the future `/security` page via a small, committed `data/pipeline-status.json` artifact (modeled on the successful NVD pattern).
   - CodeQL / secret findings in the public GitHub Security tab.
   - Scan reports and workflow definitions directly linkable from the Security Case Study page as primary evidence.
5. **Accelerates (does not block) the Cloudflare Pages migration**: CI jobs validate `_headers` early, provide a safe path for preview usage during cutover, and allow the security page to tell a clean "before/after" story.
6. **Case study artifacts**: Every gate produces referenceable proof (committed workflow source, green run URLs, SARIF artifacts, Scorecard reports) that the living security page can cite without needing external screenshots.
7. **Zero cost**: 100% free public-repo GitHub Actions minutes + Cloudflare Pages free tier (unlimited previews) + open-source tools.

### Non-Goals

- Introducing a build system or monorepo complexity (site remains a zero-build single `index.html` deploy).
- Full browser E2E tests, paid commercial scanners, or active adversarial testing.
- Automatic deployment of the `private-vault` Worker from CI (remains manual `wrangler deploy` / R2 upload; CI only validates).
- Any paid GitHub features, external SaaS accounts, or self-hosted runners.
- Altering the cyberpunk terminal UI/UX except for minimal, high-value extensions to the existing `COMMANDS` object and NVD fetch pattern.
- Exhaustive IaC scanning of `wrangler.toml` (lightweight validation only).
- Public bug bounty program or vulnerability disclosure form (explicitly out of scope per the security case study design).
- Claiming the site is "secure" — only that specific, observable, continuously verified controls are applied to this low-value, high-visibility personal system.

---

## Proposed Design

### 1. Pipeline Architecture

A single new primary workflow file: **`.github/workflows/ci.yml`**.

**Triggers** (minimal, high-signal):
- `pull_request` (opened, synchronize, reopened) targeting `main`.
- `push` to `main`.
- `workflow_dispatch` (manual full runs).
- Weekly `schedule` for deeper scans (full Scorecard + any long-running jobs).

**Concurrency**: Group by ref to auto-cancel stale runs on new pushes.

**Permissions**: Least-privilege at job level (most jobs: `contents: read`, `pull-requests: read`; security jobs add `security-events: write` only for SARIF upload).

**Jobs** (run in parallel where possible; `needs` graph for any ordering):

- `validate-site`
- `private-vault`
- `security`
- `dependency-review` (PRs only)
- `verify-headers`

A final lightweight aggregator job is optional but usually unnecessary; GitHub branch protection simply lists the required jobs.

**Mermaid Diagram: New CI/CD Flow (PR through Preview, Gates, Merge, and Production)**

```mermaid
flowchart TB
    subgraph Triggers["Event Triggers"]
        PR[Pull Request<br/>opened / synchronize]
        Push[push to main]
        Manual[workflow_dispatch<br/>or weekly schedule]
    end

    subgraph GitHubActions[".github/workflows/ci.yml<br/>concurrency: ci-${{ github.ref }}<br/>timeouts + least-privilege permissions"]
        direction TB
        V[validate-site<br/>lychee linkcheck<br/>HTML/asset hygiene<br/>_headers parse check]
        P[private-vault<br/>npm ci + typecheck<br/>npm audit<br/>wrangler --dry-run]
        S[security<br/>zizmor (Actions hardening)<br/>gitleaks<br/>CodeQL (TS/JS/Actions)<br/>osv-scanner<br/>weekly: ossf/scorecard]
        D[dependency-review<br/>(PR-only, rich diff + vulns)]
        H[verify-headers<br/>curl assertions vs _headers<br/>or against preview URL]
    end

    V & P & S & D & H -->|all must pass| Gate{Branch protection<br/>required checks}

    Gate -->|pass| Merge[Merge to main]
    Gate -->|fail| Block[PR blocked + clear failure message]

    Merge --> CFDeploy["Cloudflare Pages<br/>(GitHub integration)"]
    CFDeploy -->|main| Prod["Production<br/>martyschneider.com<br/>(headers from _headers applied)"]

    subgraph Previews["Cloudflare Pages Previews (Native & Immediate)"]
        CFApp[Cloudflare GitHub App<br/>connected to repo]
        PR -->|on creation| CFApp
        CFApp -->|instant| PreviewURL["Unique preview URL<br/>e.g. 5f3a2c1.martyschneider.pages.dev<br/>_headers + security controls active"]
        PreviewURL -->|visible in| PRComments["PR comments / Checks tab / Deployments"]
    end

    subgraph Visibility["Living Signals (for Security Case Study)"]
        Success[CI success on main] --> Update[Update data/pipeline-status.json<br/>(timestamp + run URL + per-job results)]
        Update -->|commit like NVD| Repo
        Repo --> Terminal["index.html terminal<br/>'status' command fetches<br/>(no-store) + displays"]
        Repo --> SecurityPage["Future /security page<br/>'Continuous Verification' section<br/>+ Mermaid + evidence links"]
        Repo --> Badges["README.md badges<br/>+ GitHub Security tab"]
        Repo --> GHUI["Branch protection UI<br/>+ workflow run history"]
    end

    note for Previews: Gates provide machine-enforced quality; previews provide human visual + header review in parallel. No extra deploy jobs needed in most cases.
```

**Post-migration production path** remains lightweight because CF Pages handles the actual static asset serving and header application. The CI's job is quality + evidence, not file copying.

### 2. Specific Checks (What Each Job Does)

**validate-site** (ubuntu-latest)
- `actions/checkout` (pinned SHA).
- Link integrity via `lycheeverse/lychee-action@v2` (or current) scanning `index.html` + local assets. Fail on broken internal links; configurable allowlist for external (NVD, LinkedIn, GitHub, schema.org). Produces clear "X broken links" output.
- Asset & supply-chain hygiene (simple Python/bash step or npx htmlhint):
  - Assert zero external `<script src="http` / `https` (except data: or self).
  - Verify every `@font-face` src under `fonts/` actually exists in the tree.
  - Basic structural checks (doctype, lang, canonical, no obvious exfil forms).
- `_headers` syntax / semantic validation (lightweight parser step; ensure known directives present and no obviously dangerous ones).
- Output: Fast (<2 min), clear failure messages referencing exact line or asset.

**private-vault**
- `actions/setup-node@v4` (pinned).
- `cd private-vault && npm ci`.
- `npm run typecheck` (existing).
- `npm audit --audit-level=moderate` (fail on known vulns above threshold).
- `npx wrangler deploy --dry-run` (validates wrangler.toml bindings, Worker compilation, route config without needing secrets or performing a real deploy).
- Future low-cost extension: 2–3 unit tests for `resolveKey` (export the function or test via tsx/node) under an `npm test` script. This job provides direct, living evidence for the zero-trust subsystem described in `private-vault/README.md` and the security case study.

**security** (the "impress senior DevSecOps" job)
- **zizmor** (https://github.com/zizmorcore/zizmor): Run against `.github/workflows/` (and any future). Excellent at catching unpinned actions, excessive `permissions`, template injection, and other common anti-patterns. Output SARIF or JSON; fail the job on findings. Upload SARIF via `github/codeql-action/upload-sarif` for GitHub UI.
- **gitleaks**: `gitleaks/gitleaks-action` (or docker). Full history + incremental scan. Fail on new detections. Complements GitHub's built-in secret scanning + push protection.
- **CodeQL**: Official `github/codeql-action` init + analyze for `javascript-typescript` and `actions`. Results appear as PR annotations + permanent Security tab findings. Extremely credible.
- **Dependency / OSV scanning**: `google/osv-scanner-action` or `aquasecurity/trivy-action` on `private-vault/package-lock.json` (and any future root lockfile).
- **Weekly bonus**: `ossf/scorecard-action` (scheduled). Produces a high-signal OpenSSF Scorecard report (pinned actions, security policy, etc.). Upload full report as artifact. The security case study page will link to the latest green report as primary evidence.
- All SARIF results feed the public GitHub Security tab.

**dependency-review** (PR-only)
- `actions/dependency-review-action`: Shows beautiful, scannable diff of any changed dependencies or Actions with vulnerability, license, and age data. One of the highest-ROI free checks available.

**verify-headers**
- Either:
  - Parse `_headers` + perform `curl -I` against a preview URL (when available via CF deployment context or GitHub deployment API) or a temporary local server, asserting required directives.
  - Or (initially, pre-migration): Assert against production + clearly document that `_headers` is not yet live on GH Pages + CF proxy.
- Script can be `scripts/verify-headers.py` (modeled exactly on `scripts/update_nvd_feed.py` style and structure) or a composite action.
- This job directly implements the "proposed future GitHub Action that validates header presence via curl" requested in `docs/designs/01-security-case-study.md`.

### 3. Cloudflare Pages Integration & Migration Support

**Recommended setup sequence (tied to Phase 3 rollout):**
1. Create Cloudflare Pages project (dashboard or `wrangler pages project create "martyschneider-com"`).
2. Connect the GitHub repository (recommended) or use direct + Actions for full control.
3. Build settings: **Build command empty**, **Publish directory = `/`** (root of repo). No framework.
4. Add custom domain `martyschneider.com` (and www) after DNS cutover.
5. `_headers` file is automatically respected on both production and every preview deployment.

**Preview Deployments (the killer feature):**
- The official Cloudflare GitHub App integration creates a fresh preview deployment + isolated URL for **every** PR automatically.
- Preview URLs are posted to the PR (or visible in Checks/Deployments).
- Full `_headers` (HSTS, CSP when added, etc.) + cache rules apply to previews.
- This gives instant visual QA + security header verification with zero extra CI work.
- Human reviewers can click the preview link while the machine gates are still running.

**CI + CF Coordination (low friction):**
- Do not fight the auto-deploy. Instead, protect `main` with the new required CI status checks.
- Only clean, green commits ever reach the branch that CF watches.
- Optional future hardening: GitHub Environment "production" + `cloudflare/pages-action` (or wrangler) deploy step guarded by the environment. Not required initially.
- During cutover: CI can detect hosting target and adjust header verification target accordingly.

**Private subsystem unchanged**: `learning.martyschneider.com` Worker + R2 + Access stays on its own route.

### 4. Visibility & Case Study Integration (How Results Surface)

**Core mechanism: `data/pipeline-status.json`** (modeled directly on `data/nvd-recent.json`).

Written on successful `push` to `main` by a dedicated step in ci.yml (using the same github-actions[bot] pattern as the NVD workflow). Example shape:

```json
{
  "lastVerified": "2026-05-25T20:11:00Z",
  "commit": "a1b2c3d4e5f6...",
  "workflowRunUrl": "https://github.com/marty-schneider/personal-website/actions/runs/9876543210",
  "checks": {
    "validate-site": "pass",
    "private-vault": "pass",
    "security": { "zizmor": "pass", "codeql": "pass", "gitleaks": "pass", "scorecard": "pass" },
    "verify-headers": "pass"
  },
  "previewUrl": null
}
```

**Consumption (zero new dependencies):**
- Replicate the exact `fetch(..., { cache: 'no-store' })` + graceful fallback pattern already at `index.html:2676-2680`.
- Extend the existing `COMMANDS.status` (currently around line 2597: "▮ ONLINE · NEO-CI sector 7 · pipeline OK · 0 secrets in HEAD · last build green") to incorporate real data from the JSON (e.g. "CI verified 3h ago · all gates pass · view run").
- The future `security.html` (per security case study design, delivered at `/security`) gains a prominent "Continuous Verification" or "Pipeline Evidence" section containing:
  - Live "Last verified" + clickable run link.
  - Table or cards enumerating every gate with direct links to source workflow jobs and latest green runs.
  - Embedded or linked Mermaid diagrams (the one above + a "controls catalog" diagram).
  - "Artifacts for this case study": links to the committed `ci.yml`, `SECURITY.md`, latest Scorecard report, SARIF results, etc.
  - "Hosting evolution" callout contrasting pre- and post-migration pipeline posture.

**Other surfaces:**
- New root `README.md` with status badges (e.g. `![CI](https://github.com/marty-schneider/personal-website/actions/workflows/ci.yml/badge.svg)` and security tab badge).
- GitHub repo UI itself (branch protection list, Security tab, Actions history) becomes public evidence.
- Commit status on every green main commit.

This turns the pipeline into a first-class, self-referential exhibit for the Security Case Study.

### 5. Concrete Files & Changes

**New files:**
- `.github/workflows/ci.yml` (primary artifact, ~140 lines).
- `scripts/verify-headers.py` (or keep logic lightweight inside workflow).
- `README.md` (badges, quick links to security case study and workflows, contribution notes).
- `SECURITY.md` (concise summary + pointer to `/security`, high-level threat model excerpt, "how to verify the pipeline yourself").
- `data/pipeline-status.json` (initial seed; subsequently CI-managed).
- `.github/dependabot.yml` (actions + private-vault npm weekly).

**Modified files:**
- `.github/workflows/update-nvd-feed.yml`: Pin `actions/checkout@v4` and `actions/setup-python@v5` to full 40-character SHAs (with version comments), tighten permissions if possible, add cross-reference comment to this design.
- `private-vault/package.json`: Minor script enhancements (`"ci": "npm run typecheck && npm audit..."`) and optional future test script.
- `index.html`: Small, surgical updates to the terminal `COMMANDS` object and the NVD fetch section to consume the new status JSON (graceful degradation).
- `claude.md`: Update "File Structure" and "Status" sections.
- `_headers`: (migration phase) Add phased `Content-Security-Policy-Report-Only` when safe.
- `docs/designs/01-security-case-study.md` (and summary): Add references to the implemented `ci.yml`, status artifact, and new evidence sections (minor living-document update).

**One-time repo settings:**
- Enable all public-repo security features.
- Configure branch protection on `main` with the required status checks from ci.yml.
- Connect Cloudflare Pages GitHub integration.

### 6. Example YAML Structure (Illustrative Excerpt)

(Actual file will be complete and commented.)

```yaml
name: CI

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
  workflow_dispatch:
  schedule:
    - cron: "0 14 * * 1"   # Weekly Monday deep scan

permissions: {}

jobs:
  security:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write
    steps:
      - uses: actions/checkout@<pinned-sha>  # v4
      - name: zizmor
        # ... run zizmor and upload SARIF
      - name: CodeQL
        uses: github/codeql-action/init@<pinned>
        with:
          languages: javascript-typescript, actions
      # ... analyze + gitleaks + osv-scanner
```

Similar disciplined structure for other jobs.

---

## Alternatives Considered

1. **GitHub-native only (CodeQL + Dependabot + built-in secret scanning, no extra actions)**: Lowest maintenance. Rejected — misses zizmor (highest-signal workflow linter available), explicit link/header validation, rich multi-job visible matrix, and dependency-review diffs. The "impress senior practitioner" bar would not be met.

2. **Commercial / SaaS platforms (SonarCloud free tier, Snyk, etc.)**: Strong analysis. Rejected — account overhead, potential future billing, PR comment noise, and weaker "I run this on pure public free infra" authenticity for a personal DevSecOps case study. The GitHub + Cloudflare stack is the authentic match for the portfolio's messaging.

3. **Netlify or Vercel for interim previews**: Outstanding DX and instant previews. Rejected — directly conflicts with the explicit goal of supporting the Cloudflare Pages migration without creating a second conflicting hosting narrative to document and explain.

4. **Local-only enforcement (pre-commit, husky, lint-staged)**: Excellent for developer velocity. Rejected — for a solo maintainer the centralized, auditable, always-green pipeline is the stronger signal. Optional pre-commit can be added later as a speed optimization; it is not a substitute.

5. **Status quo ("we review carefully")**: Current reality. Rejected — provides zero machine evidence, no living artifacts for the case study, and undermines the professional claims made on the site itself.

The selected design is the clear winner on signal, authenticity, migration alignment, and long-term maintainability.

---

## Security & Privacy Considerations

- **Workflow least privilege**: Every job and the top-level workflow declare the smallest possible permission set. Write access remains isolated to the two updater jobs (NVD + pipeline status).
- **Secret & credential handling**: No new long-lived secrets required initially. Any future Cloudflare API token for explicit deploys lives in a protected GitHub Environment. gitleaks + GitHub push protection + zizmor together reduce the blast radius of future workflow changes.
- **Supply chain of the pipeline**: All third-party actions are pinned to immutable SHAs (with human-readable version comments). The new dependency-review job + Dependabot will surface drift.
- **Private-vault isolation**: The `private-vault` CI job performs only read-only validation and dry-run operations. It never authenticates to R2 or Cloudflare Access, never touches private content, and produces no logs that could leak vault structure.
- **Artifact safety**: `pipeline-status.json` contains only public metadata (timestamps, SHAs, run URLs). No PII or secrets.
- **Residual risks & acceptance**: GitHub (the source of truth) remains the highest-value target. Mitigations: owner 2FA/hardware keys, optional signed commits, small attack surface of the site itself, and the fact that even a full repo compromise yields a low-value static portfolio (not customer data or production systems). The pipeline makes such an event far more likely to be noticed quickly via failed gates or anomalous status updates.
- **Auditability**: Every gate execution, finding (including suppressed), and green run is permanently recorded in GitHub. This is a feature for the Security Case Study, not a bug.

The new pipeline materially strengthens every claim made in the companion security design document.

---

## Observability & Operations

- **Day-to-day**: GitHub Actions UI + PR checks are the primary dashboard. Red X is immediately visible; logs are one click away. Email notifications for failures go to the owner account.
- **Deep signals**: GitHub Security tab (persistent findings, trends), Scorecard reports as downloadable artifacts, full SARIF.
- **Site integration** (the differentiator):
  - `data/pipeline-status.json` fetched identically to the proven NVD pattern.
  - Extended terminal `status` command.
  - Rich section on the future `/security` page.
- **Failure modes**: Fast, explicit errors. "Re-run jobs" button for transient issues. Common fixes (action version bumps) will themselves be PRs gated by the pipeline.
- **Cadence & toil**: PR gates complete in 3–6 minutes. Main runs similar. Weekly scorecard. Quarterly 20–30 minute owner review of all workflows + one manual full scan (tied to security case study review).
- **Cost & sustainability**: $0 ongoing. All tooling is free or has generous public-repo tiers.
- **Rollback & recovery**: `git revert` of a bad commit; previous green `main` is always a safe deploy source. CF Pages allows instant rollback via dashboard if needed.
- **Monitoring the monitors**: The weekly scorecard run + the security case study page itself act as meta-observability.

---

## Rollout Plan (Phased, Explicitly Tied to Cloudflare Migration)

**Phase 0 — Foundations (immediate, 1–3 days, independent of migration)**
- Add `README.md` (badges pointing forward) and `SECURITY.md`.
- Pin all actions in the existing `update-nvd-feed.yml` to full SHAs.
- Enable GitHub repository security features (Code scanning, Dependabot, Secret scanning + push protection).
- Add `.github/dependabot.yml`.
- Owner performs a self-review on a test branch + small documentation PR. Update `claude.md`.

**Phase 1 — Core Quality Gates (1 week)**
- Land `.github/workflows/ci.yml` with `validate-site`, `private-vault`, basic `security` (zizmor + gitleaks + initial CodeQL), and `dependency-review`.
- Implement lightweight `verify-headers` skeleton.
- Initially non-blocking (or required with `continue-on-error` for tuning).
- Exercise on multiple real changes. Tune allowlists and false positives.
- Begin referencing the new pipeline in the security design doc as "in progress."

**Phase 2 — Hardening & Required Status (1–2 weeks)**
- Expand `security` job with full SARIF uploads and scheduled Scorecard.
- Finalize header verification (run against live production during transition, with clear commentary).
- Configure branch protection on `main` requiring the core jobs.
- Further harden the NVD workflow.
- First high-visibility public evidence (green PRs, Security tab activity, README badges).

**Phase 3 — Cloudflare Pages Migration & Previews (aligned with hosting migration, 2–4 weeks)**
- Provision and connect Cloudflare Pages project.
- Perform DNS / custom domain cutover (reusing playbook from `private-vault/README.md`).
- Enable and validate native preview deployments.
- Update CI (conditional logic or documentation) and header verification job to target real preview URLs.
- Launch the `/security` page (per the companion design) with full "Pipeline Evidence" section, live status, and both pre- and post-migration narratives.
- Update `index.html` terminal integration and all references.

**Phase 4 — Polish, Artifacts & Living Operation (ongoing)**
- Implement `data/pipeline-status.json` updater + consumption in terminal and security page.
- Add optional SBOM step (e.g., `anchore/sbom-action`) as bonus case-study artifact.
- Add 1–3 unit tests to private-vault if desired.
- Quarterly reviews (owner + any peer feedback) of the full pipeline + security page content.
- Use the pipeline itself as the primary exhibit when sharing the portfolio.

This sequence delivers immediate value in Phase 1 while ensuring the CI story and the hosting migration reinforce each other.

---

## Open Questions

1. Preferred sequencing of Cloudflare Pages cutover relative to Phase 2 completion (owner decision on risk tolerance and timing).
2. Should header verification live as a standalone `scripts/verify-headers.py` (for symmetry with NVD) or as an inline composite/reusable action?
3. Interest level in adding a minimal test harness (2–3 tests for `resolveKey`) to `private-vault/`? (Increases signal but introduces one small dev dependency.)
4. Update mechanism for `data/pipeline-status.json`: direct bot commit on main (like NVD) vs. GitHub Release asset + occasional manual sync? (Direct commit is simpler and consistent.)
5. Future factoring: Should the Worker eventually get its own small `worker-ci.yml`, or remain inside the monorepo `ci.yml` forever?
6. Appetite for adding a single required reviewer (in addition to status checks) on `main`?
7. Desired prominence of the live CI status signal inside the main portfolio hero vs. primarily on the dedicated security page and inside the terminal?

---

## References

**Primary repository artifacts (all paths relative to repo root, current 2026-05-25 checkout):**
- NVD automation: `.github/workflows/update-nvd-feed.yml:1-37` (full file: triggers, permissions, Python invocation, conditional commit).
- Private vault implementation: `private-vault/src/worker.ts:12-17` (resolveKey traversal rejection), `private-vault/src/worker.ts:19-48` (fetch handler + privacy headers), `private-vault/wrangler.toml:1-17`, `private-vault/package.json:6-17` (existing scripts), `private-vault/README.md` (full architecture and operations).
- Edge hardening (prepared for migration): `_headers:1-25` (complete security + cache directives with explanatory comments).
- Project context & file map: `claude.md:41-82` (hosting table, tech stack, exact file structure listing `.github/workflows/update-nvd-feed.yml`, `scripts/update_nvd_feed.py`, etc.).
- Security case study foundation (the direct consumer of this work): `docs/designs/01-security-case-study.md` (esp. Background lines 33-39, Goals 51-57, Proposed Design section 3 on Mermaid, Living Aspects 103 mentioning header CI, CI/CD supply chain references) and `docs/designs/01-security-case-study-summary.md`.
- NVD data producer: `scripts/update_nvd_feed.py:1-114` (entire script; pattern to emulate for pipeline status).
- Main site client logic (to extend): `index.html:2591-2603` (COMMANDS object, especially `status` at 2597 and `gates`), `index.html:2676-2680` (NVD fetch with `cache: 'no-store'` + fallback), `index.html:1918-2680` (news ticker and terminal integration points).
- Legacy (explicitly not used in prod): `js/main.js`, `css/styles.css`.
- Other: `data/nvd-recent.json` (example of CI-managed data artifact), `.nojekyll`, `private-vault/.gitignore`.

**External references (to be cited with live links in the security page):**
- Cloudflare Pages: Preview deployments, headers configuration, GitHub integration.
- zizmor: Workflow static analysis for GitHub Actions.
- GitHub Actions security: CodeQL, dependency review action, secret scanning, Environments.
- OpenSSF Scorecard.
- lychee link checker.
- gitleaks.

All recommendations are derived directly from analysis of the actual files, the existing security design intent, and the hosting migration context. The design is concrete, phased, and ready for implementation.

---

**End of Document**