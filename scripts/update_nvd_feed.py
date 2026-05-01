#!/usr/bin/env python3
"""Fetch recent CVEs from NIST NVD API 2.0 and write data/nvd-recent.json for static site."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "nvd-recent.json"
NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
MAX_DESC = 180
RESULTS = 15


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
    try:
        data = fetch_window()
    except urllib.error.HTTPError as e:
        print(f"NVD HTTP error: {e.code} {e.reason}", file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(f"NVD URL error: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}", file=sys.stderr)
        return 1

    items = []
    for vuln in data.get("vulnerabilities") or []:
        cve = vuln.get("cve") or {}
        cid = cve.get("id")
        if not cid:
            continue
        items.append(
            {
                "cveId": cid,
                "description": description(cve),
                "severity": severity(cve),
                "lastModified": cve.get("lastModified") or "",
                "url": f"https://nvd.nist.gov/vuln/detail/{cid}",
            }
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "items": items,
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(items)} CVE(s) to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
