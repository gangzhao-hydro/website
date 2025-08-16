#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pull recent journal articles for a given ORCID from OpenAlex and save to _data/pubs_openalex.json
- Requires env: ORCID, YEARS (default 5), MAILTO (a valid email for OpenAlex policy)
- Run locally (example):
    ORCID=0000-0002-0278-502X YEARS=5 MAILTO=you@titech.ac.jp \
      python scripts/update_publications_openalex.py
"""
import os
import sys
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ORCID = os.getenv("ORCID", "").strip()
YEARS = int(os.getenv("YEARS", "5"))
MAILTO = os.getenv("MAILTO", "").strip()

OUT = Path("_data/pubs_openalex.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

if not ORCID:
    print("ERROR: ORCID env is empty. Set ORCID in the workflow or environment.")
    sys.exit(1)

if not MAILTO or "@" not in MAILTO:
    print("ERROR: MAILTO env is empty/invalid. Set repo secret OPENALEX_MAILTO to a valid email.")
    sys.exit(1)

base = "https://api.openalex.org/works"
this_year = datetime.now(timezone.utc).year
from_year = this_year - YEARS + 1

COMMON_FILTER = (
    f"authorships.author.orcid:{ORCID},"
    f"type:journal-article,"
    f"from_publication_date:{from_year}-01-01"
)

session = requests.Session()
session.headers.update({
    "User-Agent": f"OpenAlexUpdater/1.0 (+mailto:{MAILTO})",
    "From": MAILTO,
    "Accept": "application/json",
})


def doi_from(work: dict):
    doi = (work.get("ids") or {}).get("doi") or work.get("doi")
    if doi and doi.startswith("https://doi.org/"):
        return doi.replace("https://doi.org/", "")
    return doi


def venue_from(work: dict):
    hv = work.get("host_venue") or {}
    if hv.get("display_name"):
        return hv["display_name"]
    pl = (work.get("primary_location") or {}).get("source") or {}
    return pl.get("display_name")


def authors_from(work: dict):
    names = []
    for a in work.get("authorships") or []:
        author = a.get("author") or {}
        nm = author.get("display_name") or a.get("raw_author_name")
        if nm:
            names.append(nm)
    return ", ".join(names)


def fetch(per_page=200, use_select=True):
    items = []
    page = 1
    while True:
        params = {
            "filter": COMMON_FILTER,
            "sort": "publication_date:desc",
            "per-page": per_page,
            "page": page,
            "mailto": MAILTO,
        }
        if use_select:
            params["select"] = (
                "id,display_name,publication_date,doi,ids,authorships,host_venue,primary_location"
            )
        resp = session.get(base, params=params, timeout=60)
        if resp.status_code == 403:
            raise requests.HTTPError("403 Forbidden", response=resp)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if not results:
            break
        for w in results:
            items.append({
                "title": w.get("display_name"),
                "authors": authors_from(w),
                "venue": venue_from(w),
                "doi": doi_from(w),
                "publication_date": w.get("publication_date"),
            })
        page += 1
        time.sleep(0.2)  # be polite
    return items


try:
    items = fetch(per_page=200, use_select=True)
except requests.HTTPError as e:
    # 回退：减少 per-page，移除 select（有时策略更宽松）
    print(f"WARNING: initial fetch failed with {e}. Retrying with reduced params…")
    time.sleep(5)
    items = fetch(per_page=100, use_select=False)

# 去除无标题记录
items = [x for x in items if x.get("title")]

# 按日期降序（保险）
items.sort(key=lambda x: x.get("publication_date") or "", reverse=True)

OUT.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Saved {len(items)} records to {OUT}")
