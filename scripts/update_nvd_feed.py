#!/usr/bin/env python3
"""
Production-grade CVE Intelligence Feed generator for martyschneider.com

Fetches recent CVEs from NVD, enriches with:
- EPSS exploit prediction scores (api.first.org)
- CISA Known Exploited Vulnerabilities (KEV) catalog
- Personal relevance scoring for DevSecOps / security engineering work
- Product impact summaries, CWEs, etc.

Outputs a single small, rich JSON file consumed by the static site's ticker.
All enrichment happens server-side (GitHub Actions). Zero new dependencies.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

# =============================================================================
# Configuration
# =============================================================================
OUT = Path(__file__).resolve().parent.parent / "data" / "nvd-recent.json"

NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
EPSS_URL = "https://api.first.org/data/v1/epss"

MAX_DESC = 180
RESULTS = 25  # Increased for better coverage while staying small

# Relevance keywords tuned to the site owner's DevSecOps / cybersecurity focus
# (drawn from projects, terminal commands, certs, and experience log)
RELEVANCE_KEYWORDS = [
    "github action", "github actions", "workflow", "ci/cd", "cicd",
    "kubernetes", "k8s", "container", "docker", "podman",
    "terraform", "opentofu", "iac", "infrastructure as code",
    "npm", "pypi", "supply chain", "sbom", "cyclonedx", "spdx",
    "sast", "dast", "sca", "secret", "secrets", "gitleaks", "trufflehog",
    "vault", "hashicorp", "aws iam", "rbac", "policy as code",
    "argo", "helm", "eks", "aks", "gke",
    "nmap", "vulnerability scanner", "nessus", "qualys",
    "siem", "splunk", "elastic", "elk", "detection",
    "mitre att&ck", "kev", "epss",
]

# =============================================================================
# HTTP helpers (stdlib only, with retries)
# =============================================================================
def _http_get(url: str, headers: dict | None = None, timeout: int = 120, retries: int = 3) -> dict:
    """Simple GET with basic retries and exponential backoff."""
    headers = headers or {}
    headers.setdefault("Accept", "application/json")
    headers.setdefault("User-Agent", "marty-schneider-portfolio/1.0 (personal intelligence feed)")

    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError, TimeoutError) as e:
            last_err = e
            if attempt < retries - 1:
                sleep = (2 ** attempt) * 0.8
                print(f"[warn] HTTP attempt {attempt+1} failed for {url}: {e}. Retrying in {sleep:.1f}s...", file=sys.stderr)
                time.sleep(sleep)
            else:
                print(f"[error] Final failure fetching {url}: {e}", file=sys.stderr)
    raise last_err if last_err else RuntimeError(f"Failed to fetch {url}")


def iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000")


def severity(cve: dict) -> str:
    metrics = cve.get("metrics") or {}
    for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        arr = metrics.get(key)
        if not arr:
            continue
        for entry in arr:
            data = entry.get("cvssData") or {}
            sev = data.get("baseSeverity")
            if sev:
                return str(sev).upper()
            score = data.get("baseScore")
            if score is not None:
                s = float(score)
                if s >= 9.0:
                    return "CRITICAL"
                if s >= 7.0:
                    return "HIGH"
                if s >= 4.0:
                    return "MEDIUM"
                if s > 0:
                    return "LOW"
    return "UNKNOWN"


def description(cve: dict) -> str:
    for d in cve.get("descriptions") or []:
        if d.get("lang") == "en":
            val = (d.get("value") or "").replace("\n", " ").strip()
            if len(val) > MAX_DESC:
                return val[: MAX_DESC - 1].rstrip() + "…"
            return val
    return ""


def enrich_from_nvd(cve: dict) -> dict:
    """Extract richer fields from full NVD CVE object."""
    metrics = cve.get("metrics") or {}
    cvss_score = None
    cvss_version = None
    cvss_vector = None

    for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        arr = metrics.get(key) or []
        if arr:
            data = (arr[0].get("cvssData") or {})
            cvss_score = data.get("baseScore")
            cvss_version = key.replace("cvssMetric", "CVSS:")
            cvss_vector = data.get("vectorString")
            break

    cwes = []
    for weakness in (cve.get("weaknesses") or []):
        for desc in weakness.get("description") or []:
            if desc.get("lang") == "en" and desc.get("value"):
                cwes.append(desc["value"])

    products = set()
    for node in (cve.get("configurations") or []):
        for match in node.get("nodes") or []:
            for cpe in match.get("cpeMatch") or []:
                criteria = cpe.get("criteria") or ""
                if criteria.startswith("cpe:2.3:"):
                    parts = criteria.split(":")
                    if len(parts) >= 5:
                        products.add(f"{parts[3]}:{parts[4]}")

    exploit_refs = 0
    for ref in (cve.get("references") or []):
        tags = ref.get("tags") or []
        if any(t.lower() in ("exploit", "third party advisory") for t in tags):
            exploit_refs += 1

    return {
        "cvssScore": cvss_score,
        "cvssVersion": cvss_version,
        "cvssVector": cvss_vector,
        "cwes": cwes[:5],
        "products": sorted(list(products))[:3],
        "exploitEvidenceCount": exploit_refs,
        "published": cve.get("published") or "",
    }


# =============================================================================
# Enrichment helpers (KEV + EPSS + Relevance)
# =============================================================================
def fetch_kev_catalog() -> dict[str, dict]:
    """Download CISA KEV catalog once and return {cveID: entry} lookup."""
    try:
        data = _http_get(KEV_URL, timeout=60)
        catalog = {}
        for item in data.get("vulnerabilities") or []:
            cve = item.get("cveID")
            if cve:
                catalog[cve] = {
                    "dateAdded": item.get("dateAdded"),
                    "dueDate": item.get("dueDate"),
                    "requiredAction": item.get("requiredAction"),
                    "knownRansomwareCampaignUse": item.get("knownRansomwareCampaignUse"),
                    "notes": item.get("notes"),
                }
        print(f"[info] Loaded {len(catalog)} KEV entries")
        return catalog
    except Exception as e:
        print(f"[warn] Could not load CISA KEV catalog: {e}. Continuing without KEV data.", file=sys.stderr)
        return {}


def fetch_epss_scores(cve_ids: list[str]) -> dict[str, dict]:
    """Batch fetch EPSS scores. Returns {cve: {'epss': float, 'percentile': int}}."""
    if not cve_ids:
        return {}
    # EPSS supports comma-separated cve param (safe up to ~50-100)
    cve_param = ",".join(cve_ids[:60])
    url = f"{EPSS_URL}?cve={cve_param}"
    try:
        data = _http_get(url, timeout=60)
        scores = {}
        for entry in data.get("data") or []:
            cve = entry.get("cve")
            if cve:
                scores[cve] = {
                    "epss": float(entry.get("epss", 0.0)),
                    "percentile": int(float(entry.get("percentile", 0)) * 100),
                }
        print(f"[info] Got EPSS data for {len(scores)} CVEs")
        return scores
    except Exception as e:
        print(f"[warn] EPSS fetch failed: {e}. Continuing without EPSS.", file=sys.stderr)
        return {}


def compute_relevance(item: dict, keywords: list[str]) -> float:
    """Simple 0.0–1.0 relevance score for DevSecOps persona."""
    score = 0.0
    text = (item.get("description", "") + " " + " ".join(item.get("products", []))).lower()

    # Base from severity
    sev = item.get("severity", "UNKNOWN")
    if sev == "CRITICAL":
        score += 0.35
    elif sev == "HIGH":
        score += 0.25
    elif sev == "MEDIUM":
        score += 0.12

    # EPSS boost
    epss = item.get("epss") or 0.0
    if epss >= 0.5:
        score += 0.30
    elif epss >= 0.2:
        score += 0.18
    elif epss >= 0.05:
        score += 0.08

    # KEV is very strong signal
    if item.get("isKev"):
        score += 0.35

    # Keyword matches (capped)
    matches = sum(1 for kw in keywords if kw in text)
    score += min(0.22, matches * 0.055)

    return round(min(1.0, score), 3)


def derive_tags(item: dict) -> list[str]:
    tags = set()
    if item.get("isKev"):
        tags.add("kev")
    epss = item.get("epss") or 0.0
    if epss >= 0.3:
        tags.add("high-epss")
    if item.get("severity") in ("CRITICAL", "HIGH"):
        tags.add("high-severity")

    text = (item.get("description", "") + " " + " ".join(item.get("products", []))).lower()
    for kw in RELEVANCE_KEYWORDS:
        if kw in text:
            tags.add(kw.replace(" ", "-"))
            if len(tags) >= 6:
                break
    return sorted(list(tags))[:6]


# =============================================================================
# Main
# =============================================================================
def fetch_window() -> dict:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=14)
    params = (
        f"lastModStartDate={iso_z(start)}&lastModEndDate={iso_z(end)}"
        f"&resultsPerPage={RESULTS}"
    )
    url = f"{NVD_URL}?{params}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    key = os.environ.get("NVD_API_KEY", "").strip()
    if key:
        req.add_header("apiKey", key)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode())


def main() -> int:
    kev_catalog = fetch_kev_catalog()

    try:
        nvd_data = fetch_window()
    except Exception as e:
        print(f"Fatal: could not fetch NVD data: {e}", file=sys.stderr)
        return 1

    cve_ids = []
    raw_items = []
    for vuln in nvd_data.get("vulnerabilities") or []:
        cve = vuln.get("cve") or {}
        cid = cve.get("id")
        if not cid:
            continue
        cve_ids.append(cid)

        base = {
            "cveId": cid,
            "description": description(cve),
            "fullDescription": description(cve),  # will be overwritten with full if we want
            "severity": severity(cve),
            "lastModified": cve.get("lastModified") or "",
            "url": f"https://nvd.nist.gov/vuln/detail/{cid}",
        }
        base.update(enrich_from_nvd(cve))

        # KEV
        kev = kev_catalog.get(cid)
        base["isKev"] = bool(kev)
        if kev:
            base["kev"] = kev

        raw_items.append(base)

    # Batch EPSS
    epss_scores = fetch_epss_scores(cve_ids)

    # Final enrichment + relevance
    items = []
    for it in raw_items:
        epss = epss_scores.get(it["cveId"])
        if epss:
            it["epss"] = epss["epss"]
            it["epssPercentile"] = epss["percentile"]

        it["relevance"] = compute_relevance(it, RELEVANCE_KEYWORDS)
        it["tags"] = derive_tags(it)

        # Keep description short for ticker, full for modal
        if "fullDescription" not in it or not it.get("fullDescription"):
            it["fullDescription"] = it["description"]

        items.append(it)

    # Sort by relevance desc, then severity, then epss
    sev_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "UNKNOWN": 0}
    items.sort(key=lambda x: (-x.get("relevance", 0), -sev_order.get(x.get("severity"), 0), -(x.get("epss") or 0)))

    OUT.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "window": {
            "start": iso_z(datetime.now(timezone.utc) - timedelta(days=14)),
            "end": iso_z(datetime.now(timezone.utc)),
            "days": 14,
        },
        "sources": {
            "nvd": {"resultsRequested": RESULTS, "resultsReturned": len(items)},
            "epss": {"date": datetime.now(timezone.utc).strftime("%Y-%m-%d")},
            "cisaKev": {"totalInCatalog": len(kev_catalog)},
        },
        "stats": {
            "total": len(items),
            "critical": sum(1 for i in items if i.get("severity") == "CRITICAL"),
            "high": sum(1 for i in items if i.get("severity") == "HIGH"),
            "kevCount": sum(1 for i in items if i.get("isKev")),
            "highEpssCount": sum(1 for i in items if (i.get("epss") or 0) >= 0.2),
        },
        "items": items,
    }

    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(items)} enriched CVE(s) to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
