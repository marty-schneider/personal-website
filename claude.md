# Marty Schneider - Cybersecurity Portfolio Website

## Project Overview
A terminal/hacker-themed cybersecurity portfolio website for Marty Schneider,
hosted on a custom domain (`martyschneider.com`).

## Design System
"Sector 7, Neo-CI" — a cyberpunk rooftop theme. Five panels arranged on a
compass (home center; about up, experience right, projects down, connect left)
that slide into view as the "world" translates.

- **Background / ink**: Near black (#05060f, #0a0d1f)
- **Hot accent**: Neon magenta (#ff2bd6, #ff5cc8)
- **Cyan accent**: (#00f0ff, #a5f3ff)
- **Violet / amber accents**: (#b066ff, #ffae3d)
- **Text**: Off-white (#e9eaf5), muted (#7d8aa8)
- **Fonts** (self-hosted woff2 in `fonts/`): Rajdhani (UI/body), JetBrains Mono
  (terminal/mono), Major Mono Display (display), Noto Sans JP (decorative kana)
- **Navigation**: On-screen neon signs + compass HUD + arrow keys

## Pages/Sections
- [x] home (rooftop hero, neon directional signs)
- [x] about (dossier: career, stack tags, subject profile card)
- [x] experience (career timeline)
- [x] projects (security engineering artifacts)
- [x] connect (email / X / GitHub channel cards)
- [~] terminal (SDLC shell — markup commented out; JS retained behind a guard)
- [x] cyber news ticker (static curated CVE/news list)
- [ ] blog (future addition)

## Tech Stack
- Static HTML/CSS/JavaScript
- No frameworks or build tools required
- Responsive design (mobile-first)
- Fonts self-hosted as woff2 under `fonts/` (no external CDN requests)
- The on-page cyber news ticker is a static curated list baked into the page.
  The nightly NVD workflow and `data/nvd-recent.json` are retained in the repo
  but are not currently wired into the live page.

## Hosting

| Hostname | Purpose | Host |
|---|---|---|
| `martyschneider.com` (and `www`) | Public portfolio | GitHub Pages (migrating to Cloudflare Pages) |
| `learning.martyschneider.com` | Private learning module | Cloudflare Worker + R2 behind Cloudflare Access |

DNS for the apex domain is managed by Cloudflare. The private vault uses
email one-time PIN auth restricted to the owner. See
[private-vault/README.md](private-vault/README.md) for that subsystem.

## File Structure
```
/
├── index.html                       # Main single-page site (inline CSS + JS)
├── _headers                         # Cloudflare Pages security/cache headers
├── CNAME                            # GitHub Pages custom domain marker
├── .nojekyll                        # Disable Jekyll on GitHub Pages
├── fonts/                           # Self-hosted woff2 subsets (4 families)
├── css/                             # Legacy styles (not referenced by index.html)
├── js/                              # Legacy scripts (not referenced by index.html)
├── img/
│   └── rooftop.jpg                  # Cyberpunk rooftop hero / panel background
├── data/
│   └── nvd-recent.json              # CVE snapshot, refreshed nightly
├── scripts/
│   └── update_nvd_feed.py           # NVD fetch script (runs in CI)
├── .github/workflows/
│   └── update-nvd-feed.yml          # Nightly NVD refresh workflow
├── private-vault/                   # Cloudflare Worker for learning.*
│   ├── wrangler.toml
│   ├── src/worker.ts
│   ├── package.json
│   ├── tsconfig.json
│   └── README.md
└── claude.md                        # This file
```

## Status
- **Phase 1**: Core site build - done
- **Phase 2**: Content refinement, blog section - in progress
- **Phase 3**: Hosting migration to Cloudflare Pages - in progress
