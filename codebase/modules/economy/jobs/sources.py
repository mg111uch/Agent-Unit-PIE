"""JF-2 job ingestion: structured public feeds -> canonical Job dicts.

Sources: RemoteOK JSON, We Work Remotely RSS, Greenhouse/Lever/Ashby ATS APIs.
Fetchers are thin (urllib, timeouts, fail-soft []); parsers are pure and
fixture-testable. No scraping, no LinkedIn automation, per policy.
"""
from __future__ import annotations
import hashlib
import html
import json
import re
import urllib.request
from typing import Any, Dict, List
from xml.etree import ElementTree as ET

TIMEOUT = 20
SOURCES = ("remoteok", "wwr", "greenhouse", "lever", "ashby", "hasjob")


def _get(url: str) -> bytes | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "FireFlow-jobs/1.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.read()
    except Exception:
        return None


def _hid(source: str, sid: str) -> str:
    return "job_" + hashlib.sha256(f"{source}:{sid}".encode()).hexdigest()[:12]


def _remote_policy(loc: str) -> tuple:
    """Remote, India-tagged (eligible for IST candidates), or onsite."""
    loc = (loc or "").lower()
    if "remote" in loc:
        return "remote", []
    if "india" in loc:
        return "india", ["India"]
    return "onsite", []
    return "job_" + hashlib.sha256(f"{source}:{sid}".encode()).hexdigest()[:12]


def _skills_of(text: str) -> List[str]:
    vocab = ["python", "typescript", "javascript", "react", "next.js", "node",
             "rust", "go", "java", "ruby", "php", "swift", "kotlin", "flutter",
             "react native", "aws", "gcp", "azure", "docker", "kubernetes",
             "postgres", "graphql", "django", "flask", "fastapi", "vue",
             "angular", "svelte", "tailwind", "ci/cd", "terraform", "redis",
             "elasticsearch", "kafka", "rabbitmq", "grpc", "websockets",
             "esp32", "raspberry", "iot", "unity", "unreal", "godot",
             "llm", "langchain", "rag", "pytorch", "tensorflow", "ml", "ai agent"]
    t = (text or "").lower()
    return [v for v in vocab if v in t]


def parse_remoteok(raw: bytes) -> List[Dict[str, Any]]:
    """RemoteOK API list (first row is legal notice — skipped)."""
    try:
        items = json.loads(raw)
    except Exception:
        return []
    out = []
    for it in items[1:] if isinstance(items, list) else []:
        if not isinstance(it, dict) or not it.get("id"):
            continue
        desc = re.sub(r"<[^>]+>", " ", it.get("description") or "")
        out.append({"source": "remoteok", "source_job_id": str(it["id"]),
                    "company": it.get("company") or "",
                    "title": html.unescape(it.get("position") or ""),
                    "description": html.unescape(desc).strip()[:4000],
                    "skills": it.get("tags") or [],
                    "seniority": "", "employment_type": "full_time",
                    "compensation": it.get("salary_min") or 0,
                    "currency": "USD", "remote_policy": "remote",
                    "eligible_countries": [], "timezone": "",
                    "url": it.get("url") or "",
                    "posted_at": it.get("date") or ""})
    return out


def parse_wwr(raw: bytes) -> List[Dict[str, Any]]:
    """WWR category RSS -> jobs (description carries the spec)."""
    try:
        root = ET.fromstring(raw)
    except Exception:
        return []
    out = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = re.sub(r"<[^>]+>", " ", item.findtext("description") or "")
        m = re.match(r"(.+?):\s*(.+)", title)
        company, role = (m.group(1), m.group(2)) if m else ("", title)
        out.append({"source": "wwr", "source_job_id": link.rsplit("/", 2)[-2] if link else title[:40],
                    "company": company.strip(), "title": role.strip(),
                    "description": html.unescape(desc).strip()[:4000],
                    "skills": _skills_of(desc), "seniority": "",
                    "employment_type": "full_time", "compensation": 0,
                    "currency": "", "remote_policy": "remote",
                    "eligible_countries": [], "timezone": "",
                    "url": link, "posted_at": item.findtext("pubDate") or ""})
    return out


def parse_greenhouse(board: str, raw: bytes) -> List[Dict[str, Any]]:
    try:
        jobs = json.loads(raw).get("jobs", [])
    except Exception:
        return []
    out = []
    for j in jobs:
        loc = j.get("location") or {}
        pol, countries = _remote_policy(loc.get("name") or "")
        out.append({"source": "greenhouse", "source_job_id": str(j.get("id")),
                    "company": board, "title": j.get("title") or "",
                    "description": re.sub(r"<[^>]+>", " ", j.get("content") or "")[:4000],
                    "skills": _skills_of(j.get("content") or ""),
                    "seniority": "", "employment_type": "full_time",
                    "compensation": 0, "currency": "",
                    "remote_policy": pol,
                    "eligible_countries": countries, "timezone": "",
                    "url": j.get("absolute_url") or "",
                    "posted_at": j.get("updated_at") or ""})
    return out


def parse_lever(org: str, raw: bytes) -> List[Dict[str, Any]]:
    try:
        items = json.loads(raw)
    except Exception:
        return []
    out = []
    for j in items if isinstance(items, list) else []:
        cats = j.get("categories") or {}
        pol, countries = _remote_policy(cats.get("location") or "")
        out.append({"source": "lever", "source_job_id": j.get("id") or "",
                    "company": org, "title": j.get("text") or "",
                    "description": re.sub(r"<[^>]+>", " ", j.get("description") or "")[:4000],
                    "skills": (j.get("tags") or []) + _skills_of(j.get("description") or ""),
                    "seniority": "", "employment_type": "full_time",
                    "compensation": 0, "currency": "",
                    "remote_policy": pol,
                    "eligible_countries": countries, "timezone": "",
                    "url": j.get("hostedUrl") or "",
                    "posted_at": j.get("createdAt") or ""})
    return out


def parse_ashby(board: str, raw: bytes) -> List[Dict[str, Any]]:
    try:
        jobs = json.loads(raw).get("jobs", [])
    except Exception:
        return []
    out = []
    for j in jobs:
        loc = j.get("locationName") or ""
        pol, countries = _remote_policy(loc)
        out.append({"source": "ashby", "source_job_id": j.get("id") or "",
                    "company": j.get("organizationName") or board,
                    "title": j.get("title") or "",
                    "description": (j.get("descriptionPlain") or "")[:4000],
                    "skills": _skills_of(j.get("descriptionPlain") or ""),
                    "seniority": "", "employment_type": "full_time",
                    "compensation": (j.get("compensationTierSummary") or ""),
                    "currency": "", "remote_policy": pol,
                    "eligible_countries": countries, "timezone": "",
                    "url": j.get("jobUrl") or "",
                    "posted_at": j.get("publishedAt") or ""})
    return out


def parse_hasjob(raw: bytes) -> List[Dict[str, Any]]:
    """Hasjob Atom feed (India-first board): company hides in content HTML."""
    ns = {"a": "http://www.w3.org/2005/Atom"}
    try:
        root = ET.fromstring(raw)
    except Exception:
        return []
    out = []
    for e in root.findall("a:entry", ns):
        title = (e.findtext("a:title", default="", namespaces=ns) or "").strip()
        loc = (e.findtext("a:location", default="", namespaces=ns) or "").strip()
        content = e.findtext("a:content", default="", namespaces=ns) or ""
        text = re.sub(r"<[^>]+>", " ", content).strip()
        m = re.match(r"\s*(.+?)(?:Hyderabad|Bengaluru|Bangalore|Delhi|Mumbai|Chennai|Pune|Noida|Gurgaon|Kochi|Anywhere|Remote|India|$)",
                     text, re.I)
        company = (m.group(1).strip() if m else "")[:80]
        pol, countries = _remote_policy(loc)
        if pol == "onsite" and not any(w in loc.lower() for w in ("remote", "anywhere")):
            pol = "india" if loc else pol  # hasjob = Indian board; city-tagged ≈ eligible
            countries = ["India"] if pol == "india" else countries
        out.append({"source": "hasjob", "source_job_id": (e.findtext("a:id", default="", namespaces=ns) or "")[-12:],
                    "company": company, "title": title,
                    "description": html.unescape(text)[:4000],
                    "skills": _skills_of(text), "seniority": "",
                    "employment_type": "full_time", "compensation": 0,
                    "currency": "", "remote_policy": pol,
                    "eligible_countries": countries, "timezone": "",
                    "url": e.findtext("a:id", default="", namespaces=ns) or "",
                    "posted_at": e.findtext("a:published", default="", namespaces=ns) or ""})
    return out


def normalize(job: Dict[str, Any]) -> Dict[str, Any]:
    """Fill id + defaults. Raises on missing company/title."""
    if not job.get("company") or not job.get("title"):
        raise ValueError("job needs company + title")
    job = {**job, "job_id": _hid(job.get("source", "?"), str(job.get("source_job_id") or job.get("url") or job["title"]))}
    return job


def fetch(source: str, arg: str = "") -> List[Dict[str, Any]]:
    """Live fetch one source (fail-soft []). arg = board/org/category."""
    if source == "remoteok":
        raw = _get("https://remoteok.com/api")
        return [normalize(j) for j in parse_remoteok(raw or b"") if j.get("company")]
    if source == "wwr":
        raw = _get(f"https://weworkremotely.com/categories/{arg or 'remote-programming-jobs'}.rss")
        return [normalize(j) for j in parse_wwr(raw or b"") if j.get("title")]
    if source == "greenhouse":
        raw = _get(f"https://boards-api.greenhouse.io/v1/boards/{arg}/jobs?content=false")
        return [normalize(j) for j in parse_greenhouse(arg, raw or b"") if j.get("title")]
    if source == "lever":
        raw = _get(f"https://api.lever.co/v0/postings/{arg}?mode=json")
        return [normalize(j) for j in parse_lever(arg, raw or b"") if j.get("title")]
    if source == "ashby":
        raw = _get(f"https://api.ashbyhq.com/posting-api/job-board/{arg}")
        return [normalize(j) for j in parse_ashby(arg, raw or b"") if j.get("title")]
    if source == "hasjob":
        raw = _get("https://hasjob.co/feed")
        return [normalize(j) for j in parse_hasjob(raw or b"") if j.get("company") and j.get("title")]
    raise ValueError(f"source must be one of {SOURCES}")
