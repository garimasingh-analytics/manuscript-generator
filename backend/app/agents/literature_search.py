from __future__ import annotations

import asyncio
import re
from urllib.parse import quote
from typing import Any, Dict, List, Optional

import httpx


def build_query(main_keywords: List[str], exclusion_keywords: List[str], mesh_terms: List[str]) -> str:
    terms = []
    for k in (main_keywords or []):
        k = k.strip()
        if k:
            terms.append(k)
    for m in (mesh_terms or []):
        m = m.strip()
        if m:
            terms.append(f"\"{m}\"[MeSH Terms]")

    query = " AND ".join([f"({t})" for t in terms]) if terms else ""
    for ex in (exclusion_keywords or []):
        ex = ex.strip()
        if ex:
            query = f"{query} NOT ({ex})" if query else f"NOT ({ex})"
    return query.strip()


def _safe_int(v: Any) -> Optional[int]:
    try:
        if v is None:
            return None
        return int(v)
    except Exception:
        return None


def _extract_year(text: Optional[str]) -> Optional[int]:
    if not text:
        return None
    m = re.search(r"(19|20)\d{2}", text)
    return int(m.group(0)) if m else None


async def _pubmed_search(client: httpx.AsyncClient, query: str, *, retmax: int) -> List[Dict]:
    # NCBI E-utilities
    if not query:
        return []
    esearch = await client.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
        params={"db": "pubmed", "term": query, "retmode": "json", "retmax": retmax},
        timeout=30,
    )
    esearch.raise_for_status()
    ids = esearch.json().get("esearchresult", {}).get("idlist", []) or []
    if not ids:
        return []
    esummary = await client.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
        params={"db": "pubmed", "id": ",".join(ids), "retmode": "json"},
        timeout=30,
    )
    esummary.raise_for_status()
    result = esummary.json().get("result", {}) or {}

    out = []
    for pmid in ids:
        item = result.get(pmid) or {}
        title = (item.get("title") or "").strip().rstrip(".")
        if not title:
            continue
        authors = [a.get("name") for a in (item.get("authors") or []) if a.get("name")]
        year = _safe_int((item.get("pubdate") or "").split(" ")[0]) or _extract_year(item.get("pubdate"))
        journal = item.get("fulljournalname") or item.get("source")
        doi = None
        for aid in (item.get("articleids") or []):
            if aid.get("idtype") == "doi":
                doi = aid.get("value")
                break
        out.append(
            {
                "title": title,
                "authors": authors,
                "year": year,
                "journal": journal,
                "doi": doi,
                "pmid": pmid,
                "abstract": None,
                "selected": False,
                "classification": None,
                "database_source": "pubmed",
            }
        )
    return out


async def _europe_pmc_search(client: httpx.AsyncClient, query: str, *, page_size: int) -> List[Dict]:
    if not query:
        return []
    r = await client.get(
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
        params={"query": query, "format": "json", "pageSize": page_size},
        timeout=30,
    )
    r.raise_for_status()
    hits = r.json().get("resultList", {}).get("result", []) or []
    out = []
    for h in hits:
        title = (h.get("title") or "").strip().rstrip(".")
        if not title:
            continue
        authors = []
        if h.get("authorString"):
            authors = [a.strip() for a in h["authorString"].split(",") if a.strip()]
        doi = h.get("doi")
        pmid = h.get("pmid")
        year = _safe_int(h.get("pubYear"))
        journal = h.get("journalTitle")
        abstract = h.get("abstractText")
        out.append(
            {
                "title": title,
                "authors": authors,
                "year": year,
                "journal": journal,
                "doi": doi,
                "pmid": pmid,
                "abstract": abstract,
                "selected": False,
                "classification": None,
                "open_access": (str(h.get("isOpenAccess") or "").upper() == "Y")
                or (str(h.get("openAccess") or "").upper() == "Y"),
                "article_type": h.get("pubType") or h.get("resultType"),
                "database_source": "europe_pmc",
            }
        )
    return out


async def _pmc_search(client: httpx.AsyncClient, query: str, *, retmax: int) -> List[Dict]:
    # NCBI E-utilities against PMC full text IDs (PMCIDs)
    if not query:
        return []
    esearch = await client.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
        params={"db": "pmc", "term": query, "retmode": "json", "retmax": retmax},
        timeout=30,
    )
    esearch.raise_for_status()
    ids = esearch.json().get("esearchresult", {}).get("idlist", []) or []
    if not ids:
        return []
    esummary = await client.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
        params={"db": "pmc", "id": ",".join(ids), "retmode": "json"},
        timeout=30,
    )
    esummary.raise_for_status()
    result = esummary.json().get("result", {}) or {}

    out = []
    for pmcid in ids:
        item = result.get(pmcid) or {}
        title = (item.get("title") or "").strip().rstrip(".")
        if not title:
            continue
        journal = item.get("fulljournalname") or item.get("source")
        pubdate = item.get("pubdate") or ""
        year = _safe_int(str(pubdate).split(" ")[0]) or _extract_year(str(pubdate))
        authors = [a.get("name") for a in (item.get("authors") or []) if a.get("name")]
        doi = None
        for aid in (item.get("articleids") or []):
            if aid.get("idtype") == "doi":
                doi = aid.get("value")
                break
        out.append(
            {
                "title": title,
                "authors": authors,
                "year": year,
                "journal": journal,
                "doi": doi,
                "pmid": None,
                "abstract": None,
                "selected": False,
                "classification": None,
                "open_access": True,
                "article_type": None,
                "database_source": "pmc",
            }
        )
    return out


async def _crossref_search(client: httpx.AsyncClient, query: str, *, rows: int) -> List[Dict]:
    if not query:
        return []
    r = await client.get(
        "https://api.crossref.org/works",
        params={"query": query, "rows": rows},
        timeout=30,
    )
    r.raise_for_status()
    items = r.json().get("message", {}).get("items", []) or []
    out = []
    for it in items:
        title = ""
        if isinstance(it.get("title"), list) and it["title"]:
            title = it["title"][0]
        title = (title or "").strip().rstrip(".")
        if not title:
            continue
        doi = it.get("DOI")
        year = None
        if it.get("published-print", {}).get("date-parts"):
            year = _safe_int(it["published-print"]["date-parts"][0][0])
        elif it.get("published-online", {}).get("date-parts"):
            year = _safe_int(it["published-online"]["date-parts"][0][0])
        journal = None
        if isinstance(it.get("container-title"), list) and it["container-title"]:
            journal = it["container-title"][0]
        authors = []
        for a in (it.get("author") or [])[:20]:
            name = " ".join([x for x in [a.get("given"), a.get("family")] if x])
            if name:
                authors.append(name)
        out.append(
            {
                "title": title,
                "authors": authors,
                "year": year,
                "journal": journal,
                "doi": doi,
                "pmid": None,
                "abstract": None,
                "selected": False,
                "classification": None,
                "open_access": None,
                "article_type": it.get("type"),
                "database_source": "crossref",
            }
        )
    return out


async def _semantic_scholar_search(client: httpx.AsyncClient, query: str, *, limit: int) -> List[Dict]:
    if not query:
        return []
    r = await client.get(
        "https://api.semanticscholar.org/graph/v1/paper/search",
        params={
            "query": query,
            "limit": limit,
            "fields": "title,authors,year,journal,abstract,externalIds,openAccessPdf",
        },
        timeout=30,
    )
    r.raise_for_status()
    data = (r.json() or {}).get("data", []) or []
    out = []
    for it in data:
        title = (it.get("title") or "").strip().rstrip(".")
        if not title:
            continue
        authors = [a.get("name") for a in (it.get("authors") or []) if a.get("name")]
        year = _safe_int(it.get("year"))
        journal = (it.get("journal") or {}).get("name") if isinstance(it.get("journal"), dict) else None
        abstract = it.get("abstract")
        external = it.get("externalIds") or {}
        doi = external.get("DOI") or external.get("doi")
        pmid = external.get("PubMed") or external.get("PMID") or external.get("pmid")
        out.append(
            {
                "title": title,
                "authors": authors,
                "year": year,
                "journal": journal,
                "doi": doi,
                "pmid": pmid,
                "abstract": abstract,
                "selected": False,
                "classification": None,
                "open_access": bool(it.get("openAccessPdf")),
                "article_type": None,
                "database_source": "semantic_scholar",
            }
        )
    return out


async def _doaj_search(client: httpx.AsyncClient, query: str, *, page_size: int) -> List[Dict]:
    if not query:
        return []
    # DOAJ search endpoint: /api/v2/search/articles/{query}
    r = await client.get(
        f"https://doaj.org/api/v2/search/articles/{quote(query)}",
        params={"pageSize": page_size},
        timeout=30,
    )
    r.raise_for_status()
    hits = (r.json() or {}).get("results", []) or []
    out = []
    for h in hits:
        bib = (h.get("bibjson") or {})
        title = (bib.get("title") or "").strip().rstrip(".")
        if not title:
            continue
        authors = [a.get("name") for a in (bib.get("author") or []) if a.get("name")]
        year = _safe_int(bib.get("year"))
        journal = (bib.get("journal") or {}).get("title")
        doi = None
        for ident in (bib.get("identifier") or []):
            if (ident.get("type") or "").lower() == "doi":
                doi = ident.get("id")
                break
        abstract = bib.get("abstract")
        out.append(
            {
                "title": title,
                "authors": authors,
                "year": year,
                "journal": journal,
                "doi": doi,
                "pmid": None,
                "abstract": abstract,
                "selected": False,
                "classification": None,
                "open_access": True,
                "article_type": bib.get("type") or None,
                "database_source": "doaj",
            }
        )
    return out


async def _rxiv_via_europe_pmc(
    client: httpx.AsyncClient, query: str, *, source: str, page_size: int
) -> List[Dict]:
    """
    Europe PMC indexes bioRxiv/medRxiv; we filter by SRC for keyword search.
    Source values include: BIORXIV, MEDRXIV
    """
    if not query:
        return []
    q = f"({query}) AND (SRC:{source})"
    r = await client.get(
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
        params={"query": q, "format": "json", "pageSize": page_size},
        timeout=30,
    )
    r.raise_for_status()
    hits = r.json().get("resultList", {}).get("result", []) or []
    out = []
    for h in hits:
        title = (h.get("title") or "").strip().rstrip(".")
        if not title:
            continue
        authors = []
        if h.get("authorString"):
            authors = [a.strip() for a in h["authorString"].split(",") if a.strip()]
        doi = h.get("doi")
        year = _safe_int(h.get("pubYear"))
        journal = h.get("journalTitle") or source
        abstract = h.get("abstractText")
        out.append(
            {
                "title": title,
                "authors": authors,
                "year": year,
                "journal": journal,
                "doi": doi,
                "pmid": None,
                "abstract": abstract,
                "selected": False,
                "classification": None,
                "open_access": True,
                "article_type": "preprint",
                "database_source": source.lower(),
            }
        )
    return out


async def run_literature_search(
    *,
    databases: List[str],
    query: str,
    max_results_per_db: int,
) -> tuple[List[Dict], Dict[str, Any], Dict[str, str]]:
    results: List[Dict] = []
    by_db: Dict[str, Any] = {}
    errors: Dict[str, str] = {}

    async with httpx.AsyncClient(headers={"User-Agent": "ManuscriptWriter/0.1 (contact: local-dev)"}) as client:
        tasks = []

        async def wrap(db: str, coro):
            try:
                items = await coro
                by_db[db] = {"found": len(items)}
                return items
            except Exception as e:
                errors[db] = str(e)
                by_db[db] = {"found": 0}
                return []

        for db in databases:
            if db == "pubmed":
                tasks.append(wrap(db, _pubmed_search(client, query, retmax=max_results_per_db)))
            elif db == "pmc":
                tasks.append(wrap(db, _pmc_search(client, query, retmax=max_results_per_db)))
            elif db == "europe_pmc":
                tasks.append(wrap(db, _europe_pmc_search(client, query, page_size=max_results_per_db)))
            elif db == "crossref":
                tasks.append(wrap(db, _crossref_search(client, query, rows=max_results_per_db)))
            elif db == "semantic_scholar":
                tasks.append(wrap(db, _semantic_scholar_search(client, query, limit=max_results_per_db)))
            elif db == "doaj":
                tasks.append(wrap(db, _doaj_search(client, query, page_size=max_results_per_db)))
            elif db == "biorxiv":
                tasks.append(wrap(db, _rxiv_via_europe_pmc(client, query, source="BIORXIV", page_size=max_results_per_db)))
            elif db == "medrxiv":
                tasks.append(wrap(db, _rxiv_via_europe_pmc(client, query, source="MEDRXIV", page_size=max_results_per_db)))

        chunks = await asyncio.gather(*tasks) if tasks else []
        for chunk in chunks:
            results.extend(chunk)

    return results, by_db, errors

