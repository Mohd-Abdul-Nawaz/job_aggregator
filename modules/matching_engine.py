"""
matching_engine.py
-------------------
Computes a 0-100 match score between a resume's text and a job posting's
text (description + requirements combined).

Two interchangeable strategies are provided:

1. LOCAL (default, no API key needed):
   TF-IDF vectorization + cosine similarity. This is fully generic --
   it has zero hardcoded skill lists or keyword dictionaries. Whatever
   words appear in the resume and the job text drive the score. Works
   offline and is what the mock dataset uses out of the box.

2. LLM (optional, requires an API key):
   Sends the resume text and job text to an LLM and asks it to return
   a match score + a short rationale as JSON. This gives smarter,
   context-aware matching (e.g. understanding that "React" and
   "Next.js" experience is relevant to a "Frontend Engineer" role
   even if the word "Frontend" never appears in the resume).

Swap strategies via the `use_llm` flag passed into `score_job_against_resume`.
The LLM call is written against the OpenAI-compatible chat completion
schema for portability -- point `LLM_BASE_URL` at any compatible
endpoint (OpenAI, Azure OpenAI, a local vLLM server, etc.), or swap the
client block for Anthropic's SDK if you prefer Claude directly.
"""

import os
import json
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ---- LLM configuration (optional) -----------------------------------------
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")


def _combine_job_text(job_row: dict) -> str:
    """Build one text blob out of a job's description + requirements + title."""
    parts = [
        str(job_row.get("title", "")),
        str(job_row.get("description", "")),
        str(job_row.get("requirements", "")),
    ]
    return "\n".join(p for p in parts if p)


def _local_tfidf_score(resume_text: str, job_text: str) -> float:
    """
    Pure statistical similarity -- no hardcoded vocabulary.
    Returns a 0-100 float.
    """
    if not resume_text.strip() or not job_text.strip():
        return 0.0

    vectorizer = TfidfVectorizer(stop_words="english")
    try:
        tfidf_matrix = vectorizer.fit_transform([resume_text, job_text])
    except ValueError:
        # Happens if both texts are empty after stopword removal
        return 0.0

    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    return round(float(similarity) * 100, 1)


def _llm_score(resume_text: str, job_text: str) -> tuple[float, str]:
    """
    Calls an LLM to produce a nuanced match score + rationale.
    Falls back silently to the local scorer if no API key is configured
    or the call fails, so the app never breaks without an internet/API key.
    """
    if not LLM_API_KEY:
        score = _local_tfidf_score(resume_text, job_text)
        return score, "LLM key not configured -- used local TF-IDF similarity instead."

    try:
        from openai import OpenAI

        client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)

        prompt = f"""You are a recruiting-matching engine. Compare the RESUME to the JOB
POSTING below and return ONLY a JSON object with two keys:
  "score": an integer 0-100 representing how well the candidate fits the role
  "rationale": a one-sentence explanation

RESUME:
{resume_text[:6000]}

JOB POSTING:
{job_text[:4000]}
"""

        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        raw = response.choices[0].message.content.strip()

        # Strip markdown code fences if the model added them
        raw = re.sub(r"^```json|```$", "", raw, flags=re.MULTILINE).strip()
        parsed = json.loads(raw)
        return float(parsed.get("score", 0)), parsed.get("rationale", "")

    except Exception as exc:  # noqa: BLE001 -- deliberately broad: never crash the UI
        score = _local_tfidf_score(resume_text, job_text)
        return score, f"LLM call failed ({exc}); used local TF-IDF similarity instead."


def score_job_against_resume(resume_text: str, job_row: dict, use_llm: bool = False):
    """
    Public entry point used by the app.
    Returns (score: float 0-100, rationale: str)
    """
    job_text = _combine_job_text(job_row)

    if use_llm:
        return _llm_score(resume_text, job_text)

    score = _local_tfidf_score(resume_text, job_text)
    return score, "Scored via local TF-IDF text similarity (no LLM call)."


def score_all_jobs(resume_text: str, jobs_df, use_llm: bool = False):
    """
    Vectorized-ish helper: applies score_job_against_resume across an entire
    DataFrame of jobs and returns two new lists (scores, rationales) aligned
    to the DataFrame's row order.
    """
    scores, rationales = [], []
    for _, row in jobs_df.iterrows():
        s, r = score_job_against_resume(resume_text, row.to_dict(), use_llm=use_llm)
        scores.append(s)
        rationales.append(r)
    return scores, rationales
