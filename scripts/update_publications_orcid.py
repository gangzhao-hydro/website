#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fetch your own works list strictly from ORCID, then enrich via Crossref by DOI.
- No author-name heuristics, no coalesced profiles → zero false positives.
- Output: _data/pubs_orcid.json with [title, authors, venue, doi, publication_date].

ENV:
  ORCID    : e.g., 0000-0002-0278-502X
  YEARS    : integer, default 5   (keeps items with year >= current_year - YEARS + 1)
  UA_EMAIL : optional, used in User-Agent for both ORCID & Crossref
"""
import os
import sys
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import requests

ORCID   = os.getenv("ORCID", "").strip()
YEARS   = int(os.getenv("YEARS", "5"))
UA_EMAIL = os.getenv("UA_EMAIL", "").strip()

if not ORCID:
    print("ERROR: ORCID env is empty.")
    sys.exit(1)

OUT = Path("_data/pubs_orcid.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

# ---------- HTTP session ----------
s = requests.Session()
UA = "ORCID-Crossref-Updater/1.0"
if UA_EMAIL:
    UA += f" (+mailto:{UA_EMAIL})"
s.headers.update({
    "User-Agent": UA,
    "Accept": "application/json",
})

# ---------- Helpers ----------

def canon_doi(doi: str) -> str:
    if not doi:
        return ""
    doi = doi.strip()
    for pref in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.lower().startswith(pref):
            doi = doi[len(pref):]
            break
    return doi.strip().strip('/')


def orcid_works(orcid: str) -> List[Dict]:
    """Fetch works summary from ORCID public API."""
    url = f"https://pub.orcid.org/v3.0/{orcid}/works"
    hdrs = {"Accept": "application/vnd.orcid+json"}
    if UA_EMAIL:
        hdrs["User-Agent"] = UA
    r = s.get(url, headers=hdrs, timeout=60)
    r.raise_for_status()
    data = r.json()
    groups = (data.get("group") or [])
    items = []
    for g in groups:
        summaries = g.get("work-summary") or []
        for w in summaries:
            items.append(w)
    return items


def extract_from_orcid_summary(w: Dict) -> Tuple[str, str, int]:
    """Return (title, doi, year)."""
    title = (((w.get("title") or {}).get("title") or {}).get("value") or "").strip()
    # external-ids → pick DOI if any
    doi = ""
    ext = (w.get("external-ids") or {}).get("external-id") or []
    for e in ext:
        id_type = (e.get("external-id-type") or "").lower()
        val = e.get("external-id-value") or ""
        if id_type == "doi" and val:
            doi = canon_doi(val)
            break
    # year: from "publication-date" → year
    yr = 0
    pd = w.get("publication-date") or {}
    y = (pd.get("year") or {}).get("value")
    if y and str(y).isdigit():
        yr = int(y)
    return title, doi, yr


def crossref_by_doi(doi: str) -> Dict:
    url = f"https://api.crossref.org/works/{doi}"
    r = s.get(url, timeout=60)
    if r.status_code == 404:
        return {}
    r.raise_for_status()
    m = (r.json() or {}).get("message") or {}
    # Build output
    title = (" ".join((m.get("title") or [""]))).strip() or None
    container = (" ".join((m.get("container-title") or [""]))).strip() or None
    # published → choose print > online > created
    def _pick_date(msg: Dict) -> str:
        for k in ("published-print", "published", "published-online", "created"):
            part = msg.get(k) or {}
            date_parts = part.get("date-parts") or []
            if date_parts and isinstance(date_parts[0], list) and date_parts[0]:
                dp = date_parts[0]
                y = dp[0]
                m = dp[1] if len(dp) > 1 else 1
                d = dp[2] if len(dp) > 2 else 1
                return f"{y:04d}-{m:02d}-{d:02d}"
        return ""
    pub_date = _pick_date(m)
    # authors
    authors = []
    for a in (m.get("author") or []):
        given = (a.get("given") or "").strip()
        family = (a.get("family") or "").strip()
        nm = (family + (", " + given if given else "")).strip() or a.get("name") or ""
        if nm:
            authors.append(nm)
    authors_str = ", ".join(authors)
    return {
        "title": title,
        "venue": container,
        "publication_date": pub_date,
        "authors": authors_str,
        "doi": canon_doi(doi),
    }

# ---------- Main ----------
this_year = datetime.now(timezone.utc).year
cutoff = this_year - YEARS + 1

works = orcid_works(ORCID)
records: List[Dict] = []
seen = set()

for w in works:
    title0, doi0, yr0 = extract_from_orcid_summary(w)
    if yr0 and yr0 < cutoff:
        continue
    if not title0 and not doi0:
        continue
    key = doi0 or title0
    if key in seen:
        continue
    seen.add(key)

    rec = None
    if doi0:
        try:
            rec = crossref_by_doi(doi0)
            # be polite to Crossref
            time.sleep(0.2)
        except requests.RequestException as e:
            print(f"WARN: Crossref failed for {doi0}: {e}")
            rec = None
    if not rec:
        # fall back to ORCID title + year only
        rec = {
            "title": title0 or None,
            "venue": None,
            "publication_date": f"{yr0}-01-01" if yr0 else None,
            "authors": None,
            "doi": canon_doi(doi0),
        }
    records.append(rec)

# sort desc by date
records.sort(key=lambda x: x.get("publication_date") or "", reverse=True)

OUT.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Saved {len(records)} records to {OUT}")
