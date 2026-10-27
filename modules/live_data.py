"""
live_data.py
------------
Fetches REAL, currently-open job/internship listings from public job-board
APIs and normalizes them into the exact same schema as mock_data.py, so
the rest of the app (filters, matching_engine, app.py) needs zero changes
to work with live data instead of the demo dataset.

Sources wired in:
    1. RemoteOK   -- https://remoteok.com/api            (no API key needed)
    2. Arbeitnow  -- https://arbeitnow.com/api/job-board-api  (no API key needed)
    3. Adzuna     -- https://api.adzuna.com/v1/api/jobs/...   (FREE key required)

Why these three:
    - No LinkedIn/Naukri/Internshala scraping is included on purpose --
      scraping those sites generally violates their Terms of Service and
      breaks constantly since they're JS-heavy and actively anti-scraping.
    - RemoteOK and Arbeitnow have genuinely public, scrape-permitted JSON
      APIs with no key required -- good for an instant, always-working demo.
    - Adzuna aggregates listings from thousands of real boards (including
      India-specific ones) via an official API, covering the "India /
      target country" use case the app's filters are built for. It
      requires a free API key -- sign up at https://developer.adzuna.com/
      and set ADZUNA_APP_ID / ADZUNA_APP_KEY as environment variables (or
      paste them into the sidebar at runtime).

Every function below returns a list of dicts already matching the
mock_data.py schema. Any field a given API doesn't provide is filled with
a sensible neutral default (0 / False / "Not specified") rather than a
guess, so filters treat "unspecified" as "doesn't exclude this job" --
see the corresponding tweak in filters.py.
"""

import os
import requests
import pandas as pd

REQUEST_TIMEOUT = 15  # seconds -- fail fast rather than hang the UI


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
def _guess_job_type(text: str) -> str:
    """Very rough heuristic since most public APIs don't label this explicitly."""
    text = (text or "").lower()
    experienced_signals = ["senior", "lead", "principal", "3+ years", "5+ years", "staff engineer"]
    if any(signal in text for signal in experienced_signals):
        return "Experienced"
    return "Fresher / Entry-Level"


def _guess_is_internship(title: str) -> bool:
    return "intern" in (title or "").lower()


def _matches_query(query: str, *texts: str) -> bool:
    """If no query is given, everything matches. Otherwise, case-insensitive substring check."""
    if not query.strip():
        return True
    q = query.lower()
    return any(q in (t or "").lower() for t in texts)


# ---------------------------------------------------------------------------
# 1. RemoteOK
# ---------------------------------------------------------------------------
def fetch_remoteok_jobs(query: str = "", max_results: int = 25) -> list[dict]:
    """
    RemoteOK's public API returns a JSON array where the FIRST element is a
    legal/metadata notice (not a job) -- it must be skipped.
    Docs: https://remoteok.com/api
    """
    url = "https://remoteok.com/api"
    headers = {"User-Agent": "Mozilla/5.0 (JobAggregatorDemo/1.0)"}

    try:
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        raw_jobs = resp.json()
    except (requests.RequestException, ValueError) as exc:
        print(f"[live_data] RemoteOK fetch failed: {exc}")
        return []

    jobs = []
    for entry in raw_jobs:
        if not isinstance(entry, dict) or "position" not in entry:
            continue  # skips the legal-notice first element and any malformed rows

        title = entry.get("position", "")
        description = entry.get("description", "") or ""
        tags = " ".join(entry.get("tags", []) or [])

        if not _matches_query(query, title, description, tags):
            continue

        salary_min = entry.get("salary_min") or 0
        apply_url = entry.get("url") or entry.get("apply_url") or ""
        if apply_url and not apply_url.startswith("http"):
            apply_url = "https://remoteok.com" + apply_url

        jobs.append(dict(
            title=title,
            company=entry.get("company", "Unknown Company"),
            source_site="RemoteOK",
            apply_url=apply_url,
            location=entry.get("location", "Remote") or "Remote",
            country="Remote / Global",
            job_type=_guess_job_type(title + " " + description),
            is_internship=_guess_is_internship(title),
            has_ppo=False,  # not exposed by this API
            compensation=int(salary_min) if salary_min else 0,
            compensation_currency="USD",
            min_cpi_required=0.0,     # not applicable / not specified
            grad_year_required=0,      # 0 = "not specified" (see filters.py)
            description=description,
            requirements=tags if tags else "See full description.",
            posted_date=str(entry.get("date", ""))[:10],
        ))

        if len(jobs) >= max_results:
            break

    return jobs


# ---------------------------------------------------------------------------
# 2. Arbeitnow
# ---------------------------------------------------------------------------
def fetch_arbeitnow_jobs(query: str = "", max_results: int = 25) -> list[dict]:
    """
    Arbeitnow's public job-board API. Includes a mix of remote and
    Germany-based tech roles, and does label some listings as internships.
    Docs: https://arbeitnow.com/api/job-board-api
    """
    url = "https://arbeitnow.com/api/job-board-api"

    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        payload = resp.json()
        raw_jobs = payload.get("data", [])
    except (requests.RequestException, ValueError) as exc:
        print(f"[live_data] Arbeitnow fetch failed: {exc}")
        return []

    jobs = []
    for entry in raw_jobs:
        title = entry.get("title", "")
        description = entry.get("description", "") or ""
        tags = " ".join(entry.get("tags", []) or [])
        job_types_list = entry.get("job_types", []) or []

        if not _matches_query(query, title, description, tags):
            continue

        is_internship = _guess_is_internship(title) or any(
            "intern" in jt.lower() for jt in job_types_list
        )
        location = entry.get("location", "") or ("Remote" if entry.get("remote") else "Not specified")
        country = "Remote / Global" if entry.get("remote") else location

        jobs.append(dict(
            title=title,
            company=entry.get("company_name", "Unknown Company"),
            source_site="Arbeitnow",
            apply_url=entry.get("url", ""),
            location=location,
            country=country,
            job_type="Fresher / Entry-Level" if is_internship else _guess_job_type(title + " " + description),
            is_internship=is_internship,
            has_ppo=False,
            compensation=0,  # Arbeitnow doesn't expose salary data
            compensation_currency="Not specified",
            min_cpi_required=0.0,
            grad_year_required=0,
            description=description,
            requirements=tags if tags else "See full description.",
            posted_date=str(entry.get("created_at", ""))[:10],
        ))

        if len(jobs) >= max_results:
            break

    return jobs


# ---------------------------------------------------------------------------
# 3. Adzuna (requires a free API key)
# ---------------------------------------------------------------------------
def fetch_adzuna_jobs(
    query: str = "",
    country_code: str = "in",
    app_id: str = "",
    app_key: str = "",
    max_results: int = 25,
) -> list[dict]:
    """
    Adzuna aggregates real listings from thousands of boards, with good
    India coverage (country_code="in"). Requires free credentials from
    https://developer.adzuna.com/ -- pass them in directly or set
    ADZUNA_APP_ID / ADZUNA_APP_KEY environment variables.
    Docs: https://developer.adzuna.com/docs/search
    """
    app_id = app_id or os.environ.get("ADZUNA_APP_ID", "")
    app_key = app_key or os.environ.get("ADZUNA_APP_KEY", "")

    if not app_id or not app_key:
        print("[live_data] Adzuna skipped -- no ADZUNA_APP_ID/ADZUNA_APP_KEY configured.")
        return []

    url = f"https://api.adzuna.com/v1/api/jobs/{country_code}/search/1"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": max_results,
        "what": query or "software",
        "content-type": "application/json",
    }

    try:
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        payload = resp.json()
        raw_jobs = payload.get("results", [])
    except (requests.RequestException, ValueError) as exc:
        print(f"[live_data] Adzuna fetch failed: {exc}")
        return []

    jobs = []
    for entry in raw_jobs:
        title = entry.get("title", "") or ""
        description = entry.get("description", "") or ""
        company = (entry.get("company") or {}).get("display_name", "Unknown Company")
        location = (entry.get("location") or {}).get("display_name", "Not specified")
        salary_min = entry.get("salary_min") or 0

        jobs.append(dict(
            title=title,
            company=company,
            source_site="Adzuna",
            apply_url=entry.get("redirect_url", ""),
            location=location,
            country=location,
            job_type=_guess_job_type(title + " " + description),
            is_internship=_guess_is_internship(title),
            has_ppo=False,
            compensation=int(salary_min) if salary_min else 0,
            compensation_currency="INR" if country_code == "in" else "USD",
            min_cpi_required=0.0,
            grad_year_required=0,
            description=description,
            requirements="See full description on the listing page.",
            posted_date=str(entry.get("created", ""))[:10],
        ))

    return jobs


# ---------------------------------------------------------------------------
# Combined fetch used by the app
# ---------------------------------------------------------------------------
def fetch_all_live_jobs(
    query: str = "",
    country_code: str = "in",
    adzuna_app_id: str = "",
    adzuna_app_key: str = "",
    sources: list[str] | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    """
    Fetches from whichever sources are requested (default: all three) and
    returns (combined_dataframe, list_of_warning_messages).

    A warning is added (not raised) whenever a source returns nothing --
    e.g. because of a network issue or a missing Adzuna key -- so one
    failing source never breaks the rest of the app.
    """
    sources = sources or ["RemoteOK", "Arbeitnow", "Adzuna"]
    all_jobs = []
    warnings = []

    if "RemoteOK" in sources:
        jobs = fetch_remoteok_jobs(query=query)
        if not jobs:
            warnings.append("RemoteOK returned no results (network issue, or no matches for your query).")
        all_jobs.extend(jobs)

    if "Arbeitnow" in sources:
        jobs = fetch_arbeitnow_jobs(query=query)
        if not jobs:
            warnings.append("Arbeitnow returned no results (network issue, or no matches for your query).")
        all_jobs.extend(jobs)

    if "Adzuna" in sources:
        jobs = fetch_adzuna_jobs(
            query=query, country_code=country_code,
            app_id=adzuna_app_id, app_key=adzuna_app_key,
        )
        if not jobs:
            warnings.append(
                "Adzuna returned no results -- check that ADZUNA_APP_ID/ADZUNA_APP_KEY "
                "are set (sign up free at https://developer.adzuna.com/), or that your query matched anything."
            )
        all_jobs.extend(jobs)

    df = pd.DataFrame(all_jobs) if all_jobs else pd.DataFrame(columns=[
        "title", "company", "source_site", "apply_url", "location", "country",
        "job_type", "is_internship", "has_ppo", "compensation", "compensation_currency",
        "min_cpi_required", "grad_year_required", "description", "requirements", "posted_date",
    ])
    return df, warnings
