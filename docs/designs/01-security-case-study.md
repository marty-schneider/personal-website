# Design Document: Establishing martyschneider.com as a Credible Security Case Study and Living Hardening Artifact

**Version:** 1.0  
**Date:** 2026-05-25  
**Author:** Marty Schneider  
**Status:** Draft — Ready for Self-Review / Peer Feedback  
**Scope:** Public portfolio site (`martyschneider.com` and `www`) + Private learning vault (`learning.martyschneider.com`)  
**Repository:** https://github.com/marty-schneider/personal-website  
**Hosting Context:** Currently GitHub Pages (origin) fronted by Cloudflare proxy (DNS + edge); planned migration to Cloudflare Pages (full native use of `_headers` and related features)  

---

## Overview

This document designs the addition of a public **"Security & Hardening"** section (delivered as a focused page and/or deeply integrated experience) that transforms the existing cyberpunk-themed personal portfolio into a credible, living case study of applied DevSecOps and defensive engineering.

The target audience is senior security engineers, DevSecOps practitioners, hiring managers, and peers who evaluate candidates on real-world judgment rather than buzzwords. The artifact must feel authentic: it will explicitly document the site's threat model, attack surface, concrete hardening controls (with direct references to source files and configuration), residual risks with acceptance rationale, and the ongoing operational practices used to maintain it.

In-scope systems:
- The static public site (`index.html`, assets, `data/nvd-recent.json`).
- The NVD automation pipeline (`.github/workflows/`, `scripts/`).
- The private learning vault subsystem (`private-vault/` — Cloudflare Worker + R2 behind Cloudflare Access).
- Supporting configuration (`_headers`, DNS/Cloudflare setup, deployment mechanics).

Out-of-scope: The actual private content hosted in the R2 bucket, client work for employers, and any claim of formal certification or exhaustive adversarial testing.

The result will be a self-referential, low-maintenance "living artifact" that demonstrates the owner securing their own public presence with the same rigor applied professionally.

---

## Background & Motivation

The current site (see `claude.md`, `index.html`, `private-vault/README.md`) already exhibits several strong, non-trivial security signals uncommon in personal portfolios:

- **Edge hardening via `_headers`** (prepared for Cloudflare Pages): `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, restrictive `Permissions-Policy`, `Referrer-Policy: strict-origin-when-cross-origin`. Live production responses (observed 2026-05) confirm these plus Cloudflare-added headers (`server: cloudflare`, NEL/Report-To).
- **Supply-chain minimization**: All fonts (Audiowide, JetBrains Mono, Rajdhani, Aurebesh variants — 31 files under `fonts/`) are fully self-hosted as WOFF2/WOFF. No Google Fonts, no external `@font-face`, no third-party CDNs for critical rendering assets. Legacy `css/` and `js/` directories exist but are not loaded by the production `index.html`.
- **Real zero-trust private component**: `private-vault/src/worker.ts` + `wrangler.toml` implements a minimal, read-only R2-backed Worker at `learning.martyschneider.com/*`. Path traversal protection (`resolveKey` rejects `..`, `\`, leading `/`), method allow-list (GET/HEAD only), strict privacy headers (`Cache-Control: private, no-store`, `no-referrer`). All access is gated by Cloudflare Access (email one-time PIN policy limited to owner) before the Worker executes. The private HTML is **never** committed to the public repo.
- **Automated, observable supply-chain-adjacent pipeline**: `.github/workflows/update-nvd-feed.yml` (nightly cron + `workflow_dispatch`, `contents: write` permission) runs `scripts/update_nvd_feed.py`, which queries the NVD API 2.0 (using `NVD_API_KEY` secret when present), normalizes recent CVEs, and commits only `data/nvd-recent.json`. The client-side ticker in `index.html` fetches this with `cache: 'no-store'` and falls back gracefully to a curated `NEWS` array. This is a small but genuine example of "pipeline as security sensor."
- **Minimalist static architecture**: Single `index.html` (monolithic inline CSS + JS for zero-build deploy), cyberpunk "Sector 7, Neo-CI" terminal aesthetic, compass-based panel navigation, keyboard/touch support, no frameworks, no analytics pixels, no forms that exfiltrate, no external script includes.

Despite these strengths, the security posture is currently **implicit** and **scattered** across `claude.md`, the private-vault README, commit history, and live headers. Senior practitioners cannot easily evaluate the full picture, the rationale behind choices, or the owner's ability to treat a personal public system as a production asset worthy of threat modeling and continuous hardening.

**Motivation**: In a field saturated with marketing-heavy "I care about security" portfolios, a transparent, technically precise, self-referential case study is a powerful differentiator. It directly evidences DevSecOps thinking (automation, least privilege, supply chain hygiene, defense-in-depth at the edge, honest risk acceptance) applied to the attack surface the owner actually controls and exposes publicly.

---

## Goals & Non-Goals

### Goals

1. **Credibility through specificity**: Produce documentation that references real files (`_headers`, `private-vault/src/worker.ts:12`, `.github/workflows/update-nvd-feed.yml:8`, `index.html:2676`, `wrangler.toml`, `scripts/update_nvd_feed.py`, etc.) and live behavior.
2. **Living artifact**: The new section/page must be inexpensive to keep current. Changes to hardening (new header, workflow improvement, migration milestone) should be reflected with minimal friction and visible "last reviewed" signals.
3. **Authentic tone**: Technical, precise, and humble. Explicitly call out trade-offs, residual risks, and why certain "obvious" controls were deferred.
4. **Demonstrate end-to-end thinking**: Cover the full system — public static origin, edge proxy, CI/CD automation, gated private subsystem, DNS, and the human/operational processes around them.
5. **Self-referential value**: The security content itself should reinforce the site's brand (cyberpunk terminal aesthetic) while remaining scannable for busy practitioners (tables, diagrams, clear sections).
6. **Support the Cloudflare Pages migration**: The design must accelerate or at least not impede the move from GitHub Pages origin + CF proxy to native Cloudflare Pages (where `_headers` becomes authoritative).

### Non-Goals

- Formal threat modeling workshop output or paid consultant-style report.
- Adding significant new dependencies (no heavy frameworks, no external Mermaid runtime on the public page without strong justification and SRI).
- Publicly discussing or linking to the actual private vault **content**.
- Implementing active scanning, bug bounties, or public vulnerability disclosure forms at this stage.
- Claiming the site is "secure" or "hardened against APTs." The language will be "controls applied to this low-value, high-visibility personal system."
- Re-architecting the existing delightful cyberpunk UI/UX as a side effect.

---

## Proposed Design

### 1. Delivery Mechanism for the Security & Hardening Content

**Primary artifact**: A new file `security.html` (or `security/index.html`) served at `https://martyschneider.com/security` (or `/security.html` with a redirect).

- Reuses the existing visual language (color palette, font stacks via self-hosted `@font-face` declarations copied or referenced, terminal/mono aesthetic, neon accents) for brand consistency without duplicating the full heavy inline CSS.
- Standalone enough for direct deep links and print/PDF export, while offering a "return to portfolio" affordance.
- During the CF Pages migration, add a `_redirects` file (or use Cloudflare Page Rules / Transform Rules) so `/security` cleanly serves the content.
- Secondary integration points in the main experience:
  - New terminal command in `index.html` (extend the `COMMANDS` map around line 2592): `security`, `harden`, `threatmodel`, or `dossier`.
  - Prominent "SECURITY & HARDENING →" link or additional neon sign in the navigation compass / "down" panel.
  - The existing cyber news ticker and CVE feed already provide a subtle ongoing security signal; the new page will explain the pipeline behind them.

This hybrid (dedicated page + ambient integration) maximizes both professionalism and thematic fit.

### 2. Content Structure of the Security Page

The page will contain these sections (in roughly this reading order):

1. **Header / Executive Summary** — One-paragraph thesis + key stats (e.g., "4 self-hosted font families, 1 gated Worker + R2 subsystem, 0 external script origins, nightly automated CVE sensing").
2. **System Inventory & Components** — Table with columns: Component, Purpose, Key Files/Config, Owner/Maintainer, Exposure.
3. **Architecture & Trust Boundaries** — Primary Mermaid diagram (see below) + explanatory text.
4. **Threat Model** — Concise actors, assets, and STRIDE-style summary or per-boundary notes. Explicit "what the site is *not* trying to protect against."
5. **Hardening Controls Catalog** — The heart of the artifact. Categorized table or cards:
   - Edge & Transport
   - Application & Static Content
   - CI/CD & Automation Supply Chain
   - Private / Zero-Trust Subsystem
   - Operational & Transparency
   Each row includes: Control, Implementation Evidence (exact file + snippet or link to raw GitHub), Rationale, Verification Method, Status (enforced / partial / planned).
6. **Attack Surface** — Enumerated list of reachable surfaces (DNS, apex + www, data/ JSON, fonts/, the Worker route before Access, GitHub repo public surface, NVD API dependency).
7. **Residual Risks & Acceptance Rationale** — Honest list with "why this is acceptable for this system" notes.
8. **DevSecOps Practices & Cadence** — How the owner operates the system day-to-day (nightly pipeline as sensor, self-review on changes, etc.).
9. **Living Aspects & Update Process** — How the page stays fresh (manual "last hardened" date + git commit link, proposed future GitHub Action that validates header presence via curl, etc.).
10. **Appendix** — Full references, diagram source (editable Mermaid), changelog of security-relevant changes.

### 3. Mermaid Diagram: Trust Boundaries and Data Flows

The design document (and the live security page, rendered as SVG or described) will include at least this diagram:

```mermaid
flowchart TB
    subgraph Internet["Public Internet<br/>Attackers (bots, researchers, targeted)"]
        Browser[Browser / curl / Scanners]
    end

    subgraph CFEdge["Cloudflare Edge<br/>(Authoritative DNS + Proxy)"]
        direction TB
        CFProxy[Proxy / Cache / Security Headers<br/>(_headers intent + current CF rules)]
        Access[Zero Trust Access<br/>(learning.martyschneider.com)]
    end

    subgraph PublicOrigin["Public Origin<br/>(GitHub Pages today → Cloudflare Pages post-migration)"]
        Static[index.html + fonts/ + data/nvd-recent.json<br/>+ img/]
    end

    subgraph Automation["CI/CD Automation<br/>(GitHub Actions)"]
        Workflow[.github/workflows/update-nvd-feed.yml<br/>+ scripts/update_nvd_feed.py]
        Secret[NVD_API_KEY (GitHub Secret)]
    end

    subgraph External["External Data Sources"]
        NVD[NVD REST API 2.0]
    end

    subgraph Private["Private / Zero-Trust Subsystem"]
        Worker[Cloudflare Worker<br/>private-vault/src/worker.ts<br/>(R2 fetch + anti-traversal + privacy headers)]
        R2[(R2 Bucket<br/>private-vault<br/>(never in public repo))]
    end

    Browser -->|https://martyschneider.com/*| CFProxy
    Browser -->|https://learning.martyschneider.com/*| Access
    Access -->|authenticated| Worker
    Worker --> R2

    CFProxy --> PublicOrigin
    Static -->|"static assets<br/>(self-hosted fonts, no external scripts)"| Browser

    Workflow -->|scheduled + dispatch| NVD
    NVD -->|recent CVEs| Workflow
    Workflow -->|git commit| PublicOrigin

    classDef boundary fill:#0a0d1f,stroke:#ff2bd6,color:#e9eaf5
    class Internet,CFEdge,PublicOrigin,Automation,External,Private boundary
```

Additional smaller diagrams or tables can describe:
- The CVE feed client fetch path (`fetch('data/nvd-recent.json', {cache:'no-store'})` with fallback).
- The private vault request path (exact sequence from the existing `private-vault/README.md` ASCII diagram, upgraded to Mermaid).

### 4. Concrete Hardening Recommendations (Prioritized, Realistic for Solo Maintainer)

**High value, low effort (implement in rollout):**
- Add a `security.txt` (and `/.well-known/security.txt`) served via `_headers` or a small static file. Include canonical contact, preferred languages, and a link to this security page.
- Pin GitHub Actions to commit SHAs instead of tags in `update-nvd-feed.yml` (and any future workflows). Add explicit `permissions` at job level where possible.
- Introduce a minimal `SECURITY.md` at repo root (or link from the new page) that points back to the live `/security` experience.
- During CF Pages migration: ensure `_headers` is the single source of truth; remove or document any duplicate CF Transform Rules. Add `Cache-Control` and security headers for the root document itself if not already perfect.
- Add `Content-Security-Policy` (starting permissive for the inline-heavy `index.html`, then tightening as styles/JS are optionally externalized). Example starter for the security page: `default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self' https://services.nvd.nist.gov; frame-ancestors 'none';`.
- Add `Cross-Origin-Opener-Policy: same-origin` and `Cross-Origin-Embedder-Policy` where safe (test impact on the monolithic page).
- Make the NVD workflow more robust: validate JSON shape, fail the job loudly on fetch errors, consider adding a non-secret public rate-limited path or caching layer if key rotation becomes painful.

**Medium term (post-migration or next hardening sprint):**
- Add a lightweight GitHub Action (or reuse the existing schedule) that curls the production site and asserts presence of key security headers (using Python or curl + grep in CI). This creates an automated "control drift detector."
- Consider Cloudflare Access or similar lightweight gating for non-production preview deployments if CF Pages previews are enabled.
- Vendor/lock the small set of private-vault `package.json` dependencies with `package-lock.json` (already present) + periodic `npm audit` in CI.
- Document (and optionally enforce via repo rules) that the private vault `content/` directory must never be committed.

**Aspirational but realistic:**
- Once on full Cloudflare Pages + Workers platform, evaluate free-tier Bot Fight Mode + managed WAF rules for the public site (low false-positive risk for a brochure site).
- Explore immutable or content-addressed deploys (e.g., via CF Pages + custom domain + short TTL on index with manual promotion) to reduce window of a compromised GitHub Pages push.
- Add a public "pipeline status" badge or simple synthetic check link.

All recommendations are scoped to what a single maintainer can sustain alongside professional work.

### 5. Living Artifact Mechanics

- The security page will contain a prominent "This page reflects the system state as of <date>. View source / commit history for changes" footer with a direct link to the git blame or the `SECURITY.md` / design doc.
- Key control evidence links will be of the form `https://github.com/marty-schneider/personal-website/blob/main/_headers` (raw or rendered) so readers can verify instantly.
- The terminal easter eggs in `index.html` can surface high-level summaries or "view the full dossier at /security".
- Future automation (header-validation Action) will be referenced on the page itself.

---

## Alternatives Considered

1. **Publish only as GitHub repo wiki / root `SECURITY.md` rendered by GitHub**: Rejected. Loses the integrated portfolio experience, thematic consistency, and "this is how I actually run a small production system" credibility that comes from it living at the same origin with the same aesthetic and the same NVD ticker.

2. **Use a static site generator (Astro, Hugo, 11ty) just for the security content**: Rejected for this phase. Adds a build step, toolchain maintenance, and deployment complexity to a site whose primary virtue is "zero dependencies, `git push` and done." The monolithic `index.html` approach has served the project well; the security page should respect that constraint.

3. **Host the detailed security dossier exclusively inside the private vault**: Defeats the purpose. The goal is public credibility and peer evaluation.

4. **Rely on third-party security scanners / "security score" badges** (e.g., securityheaders.com, Mozilla Observatory): Useful as supplementary signals and will be linked from the page, but insufficient alone. Badges are opaque; this design produces primary-source, explainable evidence.

5. **Full interactive React/Vue dashboard with live header introspection + attack simulators**: Overkill, increases attack surface and maintenance burden, contradicts the minimalist philosophy demonstrated elsewhere.

---

## Security & Privacy Considerations

**For the live site and the new artifact itself:**

- **Transparency risk**: Detailed public documentation of controls, architecture, and residual risks gives attackers a map. Mitigation: focus on *applied controls and rationale* rather than "these 3 CVEs are unpatched in my stack" or low-level implementation secrets. The private vault content and exact Access policy details (beyond "owner-only email OTP") remain out of scope. The NVD key is never exposed.
- **CSP introduction**: The current `index.html` relies heavily on inline `<style>` and `<script>`. A strict CSP will require either nonces (complex for static) or continued use of `'unsafe-inline'` for the main portfolio (acceptable) while tightening for `security.html` (newer, more controllable content). The design explicitly calls for a phased, tested rollout.
- **Supply chain of the artifact**: The security page will link to GitHub (itself a high-value target). Readers are reminded that verifying the live site headers via `curl -I` from multiple vantage points is the ultimate ground truth.
- **Privacy of visitors**: No new tracking, cookies, or analytics introduced. The existing design (no third-party origins for critical resources) is preserved and documented as a control.
- **Private vault isolation**: The new public documentation must never inadvertently weaken the "never committed to repo" guarantee or the Cloudflare Access boundary. The design treats the two origins as having different trust levels and documents the boundary explicitly in the Mermaid diagram.

**Meta**: Writing and publishing this design document itself follows the spirit — it is a concrete artifact produced with the same care.

---

## Observability

**Current state (documented on the security page):**
- GitHub Actions UI (public) shows every NVD refresh execution, success/failure, and the exact diff committed.
- `wrangler tail` (operator-only) for the private Worker.
- Cloudflare dashboard / edge logs for both origins (when on full CF Pages, more queryable).
- Client-side fetch failures for the CVE feed are handled gracefully with the static `NEWS` fallback (visible in `index.html:2688`).
- Manual verification via `curl -I https://martyschneider.com/` and `curl -I https://learning.martyschneider.com/` (the latter yields Access challenge).

**Proposed additions (low cost):**
- Link from the security page to the GitHub Actions workflow runs for the NVD job.
- Add a simple public synthetic monitor (free tier of a service or even a GitHub Action that pings and posts status to a gist or the page itself) for the two hostnames.
- On the security page: "Header drift detector" status (initially manual; later automated) and instructions for readers to reproduce: `curl -I ... | grep -E '^(strict-transport|permissions-policy|x-content|x-frame|referrer)'`.
- Future: A minimal `/.well-known/security.txt` that also serves as a machine-readable canary.

Observability here is deliberately lightweight and operator-friendly; the goal is confidence and rapid detection of drift, not 24/7 SOC for a personal site.

---

## Rollout Plan

**Phase 0 — Foundations (complete)**: Current research, live header capture, file inventory, and this design document.

**Phase 1 — Content & Diagrams (1–1.5 weeks, solo)**:
- Draft full prose for `security.html` (or equivalent integrated section) in a working branch.
- Create final Mermaid (and optionally static SVG fallback) diagrams.
- Write `SECURITY.md` stub in repo root.
- Add `security.txt` content and wire it via `_headers` (or placeholder for migration).

**Phase 2 — Integration & Polish (1 week)**:
- Implement the delivery mechanism (new file + navigation affordances + terminal command extensions in `index.html`).
- Style the security page to feel native while remaining readable.
- Add evidence links and "last reviewed" mechanics.
- Self-test on mobile, with JS disabled, and via `curl`.

**Phase 3 — Cloudflare Pages Migration (parallel or immediately following, 1–2 weeks)**:
- Create CF Pages project from the repo.
- Point DNS (or update existing proxy records) to the Pages deployment.
- Validate that `_headers` produces the documented controls (and improve them per recommendations).
- Update all references, remove any now-redundant CF rules, confirm both public and private subsystems continue to work.
- Update `claude.md` and the security page to reflect "now on Cloudflare Pages."

**Phase 4 — Launch & Social Proof (1 week)**:
- Merge, deploy, manual verification from multiple networks.
- Publish the security page.
- Write a concise technical thread/post (X, LinkedIn, personal blog if exists) highlighting 3–4 specific choices (self-hosted fonts as supply chain control, the private vault as zero-trust personal learning demo, the NVD pipeline as lightweight ecosystem sensing, honest residual risk section).
- Monitor for (and respond to) practitioner feedback.

**Phase 5 — Living Cadence (ongoing)**:
- Any material hardening change triggers an update to the security page within the same PR or follow-up.
- Quarterly light review (30–60 min) even if no changes: re-curl headers, review recent workflow runs, bump "last reviewed."
- Proposed header-validation Action lands in Phase 5 or 6.

Total calendar time for initial credible launch: 4–6 weeks of part-time focused work, compatible with full-time professional responsibilities.

---

## Open Questions

1. **Navigation & URL strategy**: Should `/security` be a fully separate `security.html` (cleanest for deep links and professional readers) or a dynamically revealed heavy section within the existing `index.html` compass system? Hybrid is currently favored.
2. **CSP aggressiveness on day one**: How strict can we make the policy for the new security page vs. the legacy monolithic `index.html`? Should we invest in refactoring inline styles for the main site as part of this effort?
3. **Automation depth**: Is a header-validation GitHub Action worth the small maintenance cost in Phase 5, or is manual `curl` + page footer sufficient for credibility?
4. **Paid Cloudflare features**: After migration, should any budget be allocated for WAF / advanced Access / Logs? Current design assumes free-tier + paid-equivalent features that are realistically unnecessary for this workload.
5. **Scope creep on "living"**: How much live data (beyond the existing CVE ticker) should the security page surface? (Example: recent successful NVD workflow timestamp.)
6. **Long-term ownership**: If the site is eventually archived or the author changes roles, what is the minimal viable state of the security documentation?
7. **ACAO `*` header**: Currently observed in production (likely from GitHub Pages origin). Is it intentional/desirable for a static portfolio? Should it be removed or scoped during migration?

These will be resolved during Phase 1 drafting with preference for simplicity and authenticity.

---

## References

**Primary source artifacts in this repository**:
- `_headers` — Edge security and cache headers (Cloudflare Pages format).
- `private-vault/README.md` — Complete architecture and one-time setup for the zero-trust learning vault.
- `private-vault/src/worker.ts` — Request handler with `resolveKey` traversal defense and privacy headers.
- `private-vault/wrangler.toml` — Worker + R2 binding + `learning.martyschneider.com` route.
- `.github/workflows/update-nvd-feed.yml` — Nightly CVE pipeline definition and permissions.
- `scripts/update_nvd_feed.py` — NVD API client and normalizer.
- `index.html` (esp. lines ~1917 (ticker), ~2640–2688 (NVD fetch + fallback), ~2592 (COMMANDS map), font-face blocks) — Monolithic application + live data integration.
- `claude.md` — Current project context and file manifest.
- `data/nvd-recent.json` — Example output of the automation pipeline.
- `private-vault/.gitignore` — Explicit exclusion of private `content/`.

**External / Platform**:
- Cloudflare Pages Headers documentation.
- Cloudflare Zero Trust / Access self-hosted application policies.
- Cloudflare Workers + R2 bindings.
- GitHub Actions: Security hardening (permissions, pinned actions, secrets).
- NIST NVD API 2.0 reference.
- Production header observations via `curl -I https://martyschneider.com/` (2026-05-26).
- Existing private-vault ASCII architecture diagram (to be upgraded to Mermaid).

**Related Principles**:
- Least privilege at the edge (Worker + Access).
- Supply chain minimization via vendoring (fonts).
- "Pipeline as sensor" pattern (NVD automation).
- Honest risk acceptance and transparency for low-to-medium value public assets.

---

*End of Design Document. This document itself is intended to be published (or heavily excerpted) as part of the living security artifact.*

## Appendix (for implementer): Quick File Change Map

- New: `security.html` (or equivalent)
- New/updated: `_redirects` (for clean /security URL post-migration)
- New: `security.txt` + `/.well-known/security.txt` entries in `_headers`
- Modified: `index.html` (terminal commands + navigation link + small footer update)
- Modified (post-migration): DNS / Pages project settings
- New (recommended Phase 5): `.github/workflows/validate-security-headers.yml` (optional)
- Updated: `claude.md`, `SECURITY.md` (new), this design doc moved or linked into repo as `docs/security-design.md`

This map keeps changes minimal and reviewable.