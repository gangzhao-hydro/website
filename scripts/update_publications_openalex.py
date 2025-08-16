#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenAlex updater with STRICT ORCID filter:
1) Resolve your OpenAlex author ID by ORCID (tries raw and https forms),
   use compact id (e.g., A5072991521).
2) Fetch works via cursor pagination (small batches), tolerant to 403.
3) **Keep ONLY works whose authorship contains your ORCID** when STRICT_ORCID_ONLY=true.
4) Save to _data/pubs_openalex.json (title/authors/venue/doi/publication_date).

ENV:
  ORCID              : e.g., 0000-0002-0278-502X
  YEARS              : integer, default 5 (first sync can be 10)
  MAILTO             : valid email for OpenAlex (set repo secret OPENALEX_MAILTO)
  STRICT_ORCID_ONLY  : 'true' / 'false' (default 'true')
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
STRICT = (os.getenv("STRICT_ORCID_ONLY", "true").strip().lower() == 'true')

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


def has_orcid_authorship(work: Dict, orcid: str) -> bool:
    target1 = orcid
    target2 = f"https://orcid.org/{orcid}"
    for a in work.get("authorships") or []:
        author = a.get("author") or {}
        aorc = (author.get("orcid") or "").strip()
        if aorc == target1 or aorc == target2 or aorc.endswith(orcid):
            return True
    return False


def has_authorid_authorship(work: Dict, compact_id: str) -> bool:
    for a in work.get("authorships") or []:
        author = a.get("author") or {}
        aid = (author.get("id") or "").split('/')[-1]
        if aid == compact_id:
            return True
    return False


def fetch_with_cursor(author_id: str, from_year: int, journal_only=True, per_page=50) -> List[Dict]:
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
        data = get_json(BASE_WORKS, params)
        results = data.get("results", [])
        if not results:
            break
        items.extend(results)
        cursor = (data.get("meta") or {}).get("next_cursor")
        if not cursor:
            break
        time.sleep(0.15)
    return items


if __name__ == "__main__":
    this_year  = datetime.now(timezone.utc).year
    from_year  = this_year - YEARS + 1

    try:
        author_compact_id = resolve_author_id(ORCID)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print(f"Using OpenAlex author id: {author_compact_id}")

    raw = []
    # 依次放宽尝试
    for (journal_only, per_page) in [ (True,50), (True,25), (False,25) ]:
        try:
            raw = fetch_with_cursor(author_compact_id, from_year, journal_only, per_page)
            if raw:
                break
        except requests.HTTPError as e:
            print(f"WARNING: fetch failed (journal_only={journal_only}, per_page={per_page}) with {e}. Next…")
            time.sleep(3)
            continue

    if not raw:
        print("Saved 0 records to _data/pubs_openalex.json (no results).")
        OUT.write_text("[]", encoding="utf-8")
        sys.exit(0)

    # 先按年份过滤
    def yr(work):
        d = (work.get("publication_date") or "")[:4]
        return int(d) if d.isdigit() else 0
    raw = [w for w in raw if yr(w) >= from_year]

    # ★ 关键：严格 ORCID 过滤；若关闭 STRICT，则退而取 author.id 过滤
    if STRICT:
        filtered = [w for w in raw if has_orcid_authorship(w, ORCID)]
        print(f"ORCID-strict filter: {len(filtered)} / {len(raw)} kept.")
        items = filtered
    else:
        filtered1 = [w for w in raw if has_orcid_authorship(w, ORCID)]
        filtered2 = [w for w in raw if has_authorid_authorship(w, author_compact_id)]
        # 去重
        seen = set()
        items = []
        for w in filtered1 + filtered2:
            key = (w.get('id'), w.get('doi'))
            if key not in seen:
                seen.add(key)
                items.append(w)
        print(f"Hybrid filter: kept {len(items)} from {len(raw)}.")

    # 映射为简洁字段
    out = []
    seen2 = set()
    for w in items:
        key = (w.get('display_name'), doi_from(w))
        if key in seen2:
            continue
        seen2.add(key)
        out.append({
            "title": w.get("display_name"),
            "authors": authors_from(w),
            "venue": venue_from(w),
            "doi": doi_from(w),
            "publication_date": w.get("publication_date"),
        })

    out.sort(key=lambda x: x.get("publication_date") or "", reverse=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {len(out)} records to {OUT}")
