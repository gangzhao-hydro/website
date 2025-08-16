#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenAlex updater (robust against 403):
1) Resolve OpenAlex Author ID by ORCID (tries both raw and https://orcid.org/ forms),
   and use the compact id (e.g., A5072991521) to avoid URL encoding issues.
2) Fetch works by author.id using cursor pagination (smaller per-page, no select by default).
3) Auto-fallback to looser params on 403 and continue.
4) Save to _data/pubs_openalex.json for Jekyll.

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
    qp = dict(params)
    qp["mailto"] = MAILTO
    resp = session.get(url, params=qp, timeout=60)
    if resp.status_code == 403 and allow_retry403:
        print("WARNING: 403 forbidden, retrying in 15s…", file=sys.stderr)
        time.sleep(15)
        resp = session.get(url, params=qp, timeout=60)
    resp.raise_for_status()
    return resp.json()


def resolve_author_id(orcid: str) -> str:
    """Find OpenAlex author.id by ORCID. Return compact id (e.g., A5072991521)."""
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
            full_id = author.get("id")  # e.g., https://openalex.org/A5072991521
            compact = full_id.split("/")[-1]
            print(f"Resolved ORCID -> OpenAlex author: {author.get('display_name')} ({full_id})  works={author.get('works_count')}")
            return compact
    raise RuntimeError("No OpenAlex author found for this ORCID.")


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


def fetch_with_cursor(author_id: str, from_year: int, journal_only=True, per_page=50, use_select=False) -> List[Dict]:
    items: List[Dict] = []
    cursor = "*"
    while True:
        flt = [f"authorships.author.id:{author_id}", f"from_publication_date:{from_year}-01-01"]
        if journal_only:
            flt.append("type:journal-article")
        params = {
            "filter": ",".join(flt),
            "sort": "publication_date:desc",
            "per-page": per_page,
            "cursor": cursor,
        }
        if use_select:
            params["select"] = "id,display_name,publication_date,doi,ids,authorships,host_venue,primary_location"
        try:
            data = get_json(BASE_WORKS, params)
        except requests.HTTPError as e:
            # Bubble up to try another strategy
            raise e
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
        cursor = (data.get("meta") or {}).get("next_cursor")
        if not cursor:
            break
        time.sleep(0.15)
    return items


if __name__ == "__main__":
    this_year  = datetime.now(timezone.utc).year
    from_year  = this_year - YEARS + 1

    try:
        author_compact_id = resolve_author_id(ORCID)  # e.g., A5072991521
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print(f"Using OpenAlex author id: {author_compact_id}")

    # Attempt chain: conservative → broader
    attempts = [
        {"journal_only": True,  "per_page": 50, "use_select": False},
        {"journal_only": True,  "per_page": 25, "use_select": False},
        {"journal_only": False, "per_page": 25, "use_select": False},
    ]

    items: List[Dict] = []

    for cfg in attempts:
        try:
            items = fetch_with_cursor(
                author_compact_id,
                from_year,
                journal_only=cfg["journal_only"],
                per_page=cfg["per_page"],
                use_select=cfg["use_select"],
            )
            if items:
                break
        except requests.HTTPError as e:
            print(f"WARNING: fetch attempt failed ({cfg}) with {e}. Trying next…")
            time.sleep(3)
            continue

    # Final cleanup
    def yr(x):
        d = x.get("publication_date") or ""
        return int(d[:4]) if len(d) >= 4 and d[:4].isdigit() else 0

    seen = set()
    cleaned: List[Dict] = []
    for x in items:
        if yr(x) >= from_year and x.get("title"):
            key = (x.get("title"), x.get("doi"))
            if key not in seen:
                seen.add(key)
                cleaned.append(x)

    cleaned.sort(key=lambda x: x.get("publication_date") or "", reverse=True)
    OUT.write_text(json.dumps(cleaned, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {len(cleaned)} records to {OUT}")
