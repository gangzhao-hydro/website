#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, json, sys, time, math, re
from datetime import datetime, timezone
import requests
from pathlib import Path

ORCID = os.getenv("ORCID", "YOUR_ORCID_HERE")  # 形如 0000-0002-1825-0097
YEARS = int(os.getenv("YEARS", "5"))           # 近几年
OUT = Path("_data/pubs_openalex.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

if not ORCID or ORCID.startswith("YOUR_"):
    print("Please set ORCID env or edit the script with your ORCID.")
    sys.exit(0)

base = "https://api.openalex.org/works"
this_year = datetime.now(timezone.utc).year
from_year = this_year - YEARS + 1
params = {
    "filter": f"authorships.author.orcid:{ORCID},type:journal-article,from_publication_date:{from_year}-01-01",
    "sort": "publication_date:desc",
    "per-page": 200,
    "select": "id,display_name,publication_date,doi,ids,authorships,host_venue,primary_location"
}

def doi_from(work):
    # OpenAlex 里 DOI 可能在 ids.doi（完整URL）或 doi 字段
    doi = (work.get("ids") or {}).get("doi") or work.get("doi")
    if doi and doi.startswith("https://doi.org/"):
        return doi.replace("https://doi.org/", "")
    return doi

def venue_from(work):
    hv = work.get("host_venue") or {}
    if hv.get("display_name"): 
        return hv["display_name"]
    pl = (work.get("primary_location") or {}).get("source") or {}
    return pl.get("display_name")

def authors_from(work):
    names = []
    for a in work.get("authorships") or []:
        nm = (a.get("author") or {}).get("display_name")
        if nm: names.append(nm)
    return ", ".join(names)

items, page = [], 1
while True:
    resp = requests.get(base, params={**params, "page": page, "mailto": "[email protected]"}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results", [])
    for w in results:
        items.append({
            "title": w.get("display_name"),
            "authors": authors_from(w),
            "venue": venue_from(w),
            "doi": doi_from(w),
            "publication_date": w.get("publication_date")
        })
    if len(results) == 0 or page >= data.get("meta", {}).get("count", 0) // params["per-page"] + 1:
        break
    page += 1
    time.sleep(0.5)

# 只保留有题目的
items = [x for x in items if x["title"]]
OUT.write_text(json.dumps(items, ensure_ascii=False, indent=2))
print(f"Saved {len(items)} records to {OUT}")
