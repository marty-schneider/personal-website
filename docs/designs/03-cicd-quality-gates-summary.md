# Summary: Design for CI/CD Quality Gates, Security Checks, and Preview Deployments on martyschneider.com

**Goal**: Add a credible, senior-DevSecOps-grade CI/CD pipeline (quality gates + security scanning + preview deployments) to the currently unguarded GitHub Pages + Cloudflare proxy static portfolio repo, while accelerating the planned migration to native Cloudflare Pages. The pipeline must produce living, referenceable artifacts that power the existing "Security & Hardening Case Study" effort.

**Current State (2026-05-25 checkout)**: Single workflow (`.github/workflows/update-nvd-feed.yml` for nightly NVD CVE snapshots), static `index.html` (zero-build, self-hosted fonts/assets, legacy css/js unused), prepared but inactive `_headers`, `private-vault/` (real TS Cloudflare Worker + R2 behind Access with strong anti-traversal logic at `src/worker.ts:12`), zero PR checks, no previews, no scanning. Strong foundation in other areas; explicit gaps called out in `docs/designs/01-security-case-study.md`.

**Core Deliverables**:
- Primary new artifact: `.github/workflows/ci.yml` (least-privilege, parallel jobs, pinned actions).
- Supporting: `scripts/verify-headers.py`, `data/pipeline-status.json` (CI-managed "last verified" artifact modeled on NVD feed), `README.md` (badges), `SECURITY.md`, `.github/dependabot.yml`.
- Minor enhancements to existing NVD workflow (SHA pinning), `index.html` terminal (status command), `private-vault/package.json`, and the security case study docs.

**Key Technical Recommendations** (chosen for real signal + low solo friction + free tiers):
- **Jobs**: `validate-site` (lychee link checking + asset hygiene + _headers validation), `private-vault` (npm ci + existing typecheck + audit + wrangler --dry-run), `security` (zizmor for workflow hardening, gitleaks, CodeQL for TS/JS/Actions with SARIF, osv-scanner, weekly ossf/scorecard), `dependency-review` (PR-only), `verify-headers` (curl assertions — directly fulfills request in the security design doc).
- **Previews & Migration**: Rely on Cloudflare Pages native GitHub integration for automatic, zero-extra-work PR preview deployments (unique URLs with full `_headers` applied). Protect `main` via branch protection + required CI checks so only green commits reach CF production. No fight with auto-deploy.
- **Visibility (for case study)**: `data/pipeline-status.json` updated on main success; consumed via the exact `fetch(..., {cache:'no-store'})` pattern already at `index.html:2676`. Extended terminal `status` command + rich "Continuous Verification" section on future `/security` page (with run links, Mermaid diagrams, direct evidence to `ci.yml`, SARIF, Scorecard reports).
- **Impressive extras**: All actions pinned to SHAs + Dependabot; zizmor (highest-ROI workflow scanner); public GitHub Security tab as exhibit; least-privilege permissions everywhere.

**Mermaid Diagrams Included**: Full PR → gates (parallel) → previews (CF native) → merge → production + visibility update flow; trust boundaries align with the existing security case study diagram.

**Rollout (4 phases, tightly coupled to CF migration)**:
- Phase 0 (immediate): README/SECURITY.md, pin existing actions, enable GitHub security features.
- Phase 1 (1 wk): Core ci.yml gates (non-blocking initially).
- Phase 2 (1-2 wk): Full security jobs + required branch protection.
- Phase 3 (migration window): CF Pages cutover, native previews activated, header verification against real previews, `/security` page launch with live pipeline evidence.
- Phase 4 (ongoing): Status artifact + terminal integration, quarterly reviews.

**Alternatives Rejected**: GitHub-native-only (insufficient signal), commercial SaaS (friction + inauthenticity), Netlify/Vercel previews (conflicts with CF migration goal), local pre-commit only (weaker centralized evidence).

**Security/Privacy/Operations**: Least-privilege workflows, isolated write perms, no new secrets initially, private-vault job is read-only/dry-run only, $0 cost, GitHub Actions + CF free tier, excellent audit trail via Security tab + artifacts (perfect for case study).

**Files Produced**:
- Full design: `/tmp/grok-design-doc-79ea857b.md` (comprehensive, ~structure-complete, heavily cited to real paths/lines: update-nvd-feed.yml, private-vault/src/worker.ts, _headers, claude.md, index.html:2591-2680, both security design docs, etc.).
- This concise summary: `/tmp/grok-design-summary-79ea857b.md`.

The design turns the repo's own deployment process into a first-class, self-referential DevSecOps exhibit that materially strengthens the credibility of the Security Case Study while keeping everything sustainable for one maintainer and aligned with the Cloudflare Pages migration. It is specific, phased, and ready for execution.