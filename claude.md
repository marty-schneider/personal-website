# Marty Schneider - Cybersecurity Portfolio Website

## Project Overview
A terminal/hacker-themed cybersecurity portfolio website for Marty Schneider,
hosted on a custom domain (`martyschneider.com`).

## Design System
- **Background**: Near black (#0a0e17)
- **Primary accent**: Electric blue (#00d9ff)
- **Secondary accent**: Sky blue (#0ea5e9)
- **Text**: Light gray/white (#e2e8f0, #94a3b8)
- **Font**: JetBrains Mono / Courier New (monospace)
- **Navigation**: Terminal-style with `~/` and `>` symbols

## Pages/Sections
- [x] Hero (name, title, typing animation, social links)
- [x] whoami (about/intro - career transition to cybersecurity)
- [x] experience (work history)
- [x] certifications (security certs)
- [x] projects (security projects, CTF writeups)
- [x] contact (contact form / info)
- [x] terminal (CVE widget pulling from local NVD snapshot)
- [ ] blog (future addition)

## Tech Stack
- Static HTML/CSS/JavaScript
- No frameworks or build tools required
- Responsive design (mobile-first)
- Nightly GitHub Actions workflow refreshes `data/nvd-recent.json` from the
  NIST NVD API for the terminal CVE widget

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
├── index.html                       # Main single-page site
├── _headers                         # Cloudflare Pages security/cache headers
├── CNAME                            # GitHub Pages custom domain marker
├── .nojekyll                        # Disable Jekyll on GitHub Pages
├── css/
│   └── styles.css                   # All styles
├── js/
│   └── main.js                      # Typing effect, mobile nav, fade-ins
├── img/                             # Profile photo + section panel images
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
