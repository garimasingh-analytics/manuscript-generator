from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple


def _norm_title(title: str) -> str:
    t = (title or "").strip().lower()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[^a-z0-9 ]+", "", t)
    return t


def _norm_doi(doi: Optional[str]) -> Optional[str]:
    if not doi:
        return None
    d = doi.strip().lower()
    d = d.replace("https://doi.org/", "").replace("http://doi.org/", "").replace("doi:", "").strip()
    return d or None


def make_dedupe_key(paper: Dict) -> Tuple[str, str]:
    doi = _norm_doi(paper.get("doi"))
    if doi:
        return ("doi", doi)
    pmid = (paper.get("pmid") or "").strip()
    if pmid:
        return ("pmid", pmid)
    title = _norm_title(paper.get("title") or "")
    return ("title", title)


def dedupe_papers(papers: List[Dict]) -> List[Dict]:
    seen = {}
    out = []
    for p in papers:
        k = make_dedupe_key(p)
        if not k[1]:
            # if no meaningful key, keep it (rare)
            out.append(p)
            continue
        if k in seen:
            # merge: prefer fields that are missing
            existing = seen[k]
            for field in ("doi", "pmid", "abstract", "journal", "year"):
                if not existing.get(field) and p.get(field):
                    existing[field] = p[field]
            # preserve user selections/classifications if either has them
            if p.get("selected") and not existing.get("selected"):
                existing["selected"] = True
            if p.get("classification") and not existing.get("classification"):
                existing["classification"] = p.get("classification")
            # keep a single database_source if present; otherwise preserve first
            continue
        seen[k] = p
        out.append(p)
    return out

