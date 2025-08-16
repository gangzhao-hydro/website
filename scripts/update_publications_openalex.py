#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenAlex updater (robust):
1) Resolve OpenAlex Author ID by ORCID (tries both raw and https://orcid.org/ forms)
2) Fetch works by author.id (journal articles in the last N years), with fallbacks
3) Save to _data/pubs_openalex.json  for Jekyll to render

ENV:
  ORCID  : e.g., 0000-0002-0278-502X
  YEARS  : integer, default 5 (first sync can use 10)
  MAILTO : a valid email, required by OpenAlex; also set in User-Agent/From
"""
import os
import sys
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict

import requests

ORCID  = os.getenv("ORCID", "").strip()
YEARS  = int(os.getenv("YEARS", "5"))
MAILTO = os.getenv("MAILTO", "").strip()

OUT = Path("_data/pubs_openalex.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

if not ORCID:
    print("ERROR: ORCID env is empty. Set ORCID in the workflow or environment.")
    sys.exit(1)
if not MAILTO or "@" not in MAILTO:
    print("ERROR: MAILTO env is empty/invalid. Set repo secret OPENALEX_MAILTO to a valid email.")
    sys.exit(1)

BASE_AUTHORS = "https://api.openalex.org/authors"
BASE_WORKS   = "https://api.openalex.org/works"

session = requests.Session()
session.headers.update({
    "User-Agent": f"OpenAlexUpdater/1.0 (+mailto:{MAILTO})",
    "From": MAILTO,
    "Accept": "application/json",
})


def get_json(url: str, params: Dict, allow_retry403=True):
    """GET JSON with basic 403 retry."""
    params = dict(params)
    params["mailto"] = MAILTO
    resp = session.get(url, params=params, timeout=60)
    if resp.status_code == 403 and allow_retry403:
        print("WARNING: 403 forbidden, retrying in 20s…", file=sys.stderr)
        time.sleep(20)
        resp = session.get(url, params=params, timeout=60)
    resp.raise_for_status()
    return resp.json()


def resolve_author_id(orcid: str) -> str:
    """Find OpenAlex author.id by ORCID. Try both raw and https scheme."""
    for q in (orcid, f"https://orcid.org/{orcid}"):
        data = get_json(BASE_AUTHORS, {
            "filter": f"orcid:{q}",
            "select": "id,display_name,works_count,orcid",
            "per-page": 1,
            "page": 1,
        })
        results = data.get("results", [])
        if results:
            author = results[0]
            print(f"Resolved ORCID -> OpenAlex author: {author.get('display_name')} ({author.get('id')})  works={author.get('works_count')}")
            return author["id"]  # e.g., "https://openalex.org/A1969205031"
    raise RuntimeError("No OpenAlex author found for this ORCID. Check ORCID or try widening YEARS.")


def doi_from(work: Dict):
    doi = (work.get("ids") or {}).get("doi") or work.get("doi")
    if doi and doi.startswith("https://doi.org/"):
        return doi.replace("https://doi.org/", "")
    return doi


def venue_from(work: Dict):
    hv = work.get("host_venue") or {}
    if hv.get("display_name"):
        return hv["display_name"]
    pl = (work.get("primary_location") or {}).get("source") or {}
    return pl.get("display_name")


def authors_from(work: Dict):
    names = []
    for a in work.get("authorships") or []:
        author = a.get("author") or {}
        nm = author.get("display_name") or a.get("raw_author_name")
        if nm:
            names.append(nm)
    return ", ".join(names)


def fetch_works_by_author(author_id: str, from_year: int, journal_only=True, per_page=200, use_select=True) -> List[Dict]:
    items, page = [], 1
    flt = [f"authorships.author.id:{author_id}", f"from_publication_date:{from_year}-01-01"]
    if journal_only:
        flt.append("type:journal-article")
    filt_str = ",".join(flt)
    while True:
        params = {
            "filter": filt_str,
            "sort": "publication_date:desc",
            "per-page": per_page,
            "page": page,
        }
        if use_select:
            params["select"] = "id,display_name,publication_date,doi,ids,authorships,host_venue,primary_location"
        data = get_json(BASE_WORKS, params)
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
        time.sleep(0.2)
    return items


if __name__ == "__main__":
    this_year  = datetime.now(timezone.utc).year
    from_year  = this_year - YEARS + 1

    try:
        author_id = resolve_author_id(ORCID)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print(f"Using OpenAlex author id: {author_id}")

    # Pass 1: journal articles with select/per-page=200
    items = fetch_works_by_author(author_id, from_year, journal_only=True, per_page=200, use_select=True)

    # Fallback 1: if empty, drop 'select'
    if not items:
        print("Fallback: retry without 'select' …")
        items = fetch_works_by_author(author_id, from_year, journal_only=True, per_page=100, use_select=False)

    # Fallback 2: if still empty, include all types
    if not items:
        print("Fallback: include all types (not only journal-article) …")
        items = fetch_works_by_author(author_id, from_year, journal_only=False, per_page=100, use_select=False)

    # Final sanity: filter by year >= from_year, drop empties/dupes
    def yr(x):
        d = x.get("publication_date") or ""
        return int(d[:4]) if len(d) >= 4 and d[:4].isdigit() else 0

    seen = set()
    cleaned = []
    for x in items:
        if yr(x) >= from_year and x.get("title"):
            key = (x.get("title"), x.get("doi"))
            if key not in seen:
                seen.add(key)
                cleaned.append(x)

    cleaned.sort(key=lambda x: x.get("publication_date") or "", reverse=True)
    OUT.write_text(json.dumps(cleaned, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {len(cleaned)} records to {OUT}")
