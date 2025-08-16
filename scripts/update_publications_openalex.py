#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pull recent journal articles for a given ORCID from OpenAlex and save to _data/pubs_openalex.json
- Requires env: ORCID, YEARS (default 5), MAILTO (a valid email for OpenAlex policy)
- Run locally:  ORCID=0000-0002-0278-502X MAILTO=you@titech.ac.jp python scripts/update_publications_openalex.py
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

if not MAILTO:
    print("ERROR: MAILTO env is empty. Set repo secret OPENALEX_MAILTO with your email.")
    sys.exit(1)

base = "https://api.openalex.org/works"
this_year = datetime.now(timezone.utc).year
from_year = this_year - YEARS + 1

params = {
    # 仅拉 journal-article；如需包含 in-press / early access，OpenAlex 仍标记为 journal-article
    "filter": f"authorships.author.orcid:{ORCID},type:journal-article,from_publication_date:{from_year}-01-01",
    "sort": "publication_date:desc",
    "per-page": 200,
    "select": "id,display_name,publication_date,doi,ids,authorships,host_venue,primary_location",
}

HEADERS = {
    "User-Agent": f"gh:{os.getenv('GITHUB_REPOSITORY', 'user/site')} (mailto:{MAILTO})",
    "Accept": "application/json",
}

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

items = []
page = 1

while True:
    params_req = {**params, "page": page, "mailto": MAILTO}
    try:
        resp = requests.get(base, params=params_req, headers=HEADERS, timeout=60)
        if resp.status_code == 403:
            print("OpenAlex 403：邮箱或UA校验失败，30秒后重试一次…")
            time.sleep(30)
            resp = requests.get(base, params=params_req, headers=HEADERS, timeout=60)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"ERROR: request failed at page {page}: {e}")
        sys.exit(1)

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
    # 轻微间隔，避免触发速率限制
    time.sleep(0.2)

# 仅保留有标题的记录
items = [x for x in items if x.get("title")]

OUT.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Saved {len(items)} records to {OUT}")
