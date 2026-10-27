# Universal Job & Internship Aggregator

A dynamic, resume-driven job/internship dashboard: upload a resume, get
every listing AI-ranked by fit, filter by country/skills/compensation/CPI
cutoffs, and pre-fill (not blindly auto-submit) applications via a
Playwright automation skeleton.

## Setup

```bash
cd job_aggregator
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium     # downloads the browser binary Playwright needs
```

Optional, for LLM-based matching (instead of the built-in local TF-IDF
similarity, which works with zero setup):

```bash
export LLM_API_KEY="sk-..."
export LLM_MODEL="gpt-4o-mini"          # or any OpenAI-compatible model
export LLM_BASE_URL="https://api.openai.com/v1"   # or a compatible endpoint
```

Then toggle "Use LLM for smarter matching" on in the sidebar.

## Run

```bash
streamlit run app.py
```

## What's real vs. what's a skeleton

| Piece | Status |
|---|---|
| Resume parsing (PDF/DOCX) | Fully functional |
| Local TF-IDF match scoring + ranked sort | Fully functional |
| LLM match scoring | Functional if you supply an API key; falls back gracefully otherwise |
| Filters (country, skills, type, PPO, comp, grad year, CPI) | Fully functional |
| Mock job dataset | 12 sample listings for demoing the UI — **apply links are fake placeholders, they don't go anywhere** |
| **Live job dataset** | **Real, currently-open listings with real apply links**, pulled from RemoteOK + Arbeitnow (no signup needed) and Adzuna (free signup). Toggle "Live Jobs (Real APIs)" in the sidebar and click "Fetch Live Jobs Now". |
| User Profile tab | Fully functional (stored as local JSON — see security note below) |
| Auto-apply automation | **Skeleton.** Opens the real page, fuzzy-matches form fields to your profile, fills them, and uploads your resume — but stops short of clicking Submit unless you explicitly set `auto_submit=True` |

## Getting real, working apply links (important)

By default the dashboard loads the mock dataset, whose `apply_url` values
are placeholders (`example.com/...`) meant only to demo the ranking/filter
UI — **clicking Apply on those will fail**, which is what you ran into.

To see real listings you can actually open and apply to:

1. In the sidebar, under **🌐 Data Source**, select **"Live Jobs (Real APIs)"**.
2. Enter search keywords (e.g. `python developer`, `data analyst intern`).
3. RemoteOK and Arbeitnow work immediately, no signup required.
4. For Adzuna (best India coverage), sign up free at
   https://developer.adzuna.com/, grab your `app_id` and `app_key`, and
   either paste them into the sidebar's "Adzuna API credentials" expander
   or set them as environment variables:
   ```bash
   export ADZUNA_APP_ID="your_id"
   export ADZUNA_APP_KEY="your_key"
   ```
5. Click **"Fetch Live Jobs Now"**. The dashboard will replace the mock
   data with real listings — every `apply_url` is a genuine link to that
   job's real application page.

Note: RemoteOK/Arbeitnow skew toward remote and tech-focused roles since
that's what their public APIs expose; Adzuna covers a much broader range
of roles and locations, including India-specific searches.

## Replacing mock data with a real scraper

Everything downstream (`filters.py`, `matching_engine.py`, `app.py`) is
written against the column schema documented at the top of
`modules/mock_data.py`. Point a real scraper or job-board API at that
same schema and drop it into `st.session_state.jobs_df` — no other code
changes needed.

## Important notes on the auto-apply feature

- **No two application forms are alike.** The field-matching in
  `modules/auto_apply.py` uses fuzzy string matching against labels/
  placeholders/names — it works well on straightforward forms and will
  need supervision (or a per-site tweak) on complex multi-step or
  heavily JavaScript-driven ones.
- **Terms of Service.** Many job boards (LinkedIn, Indeed, etc.)
  restrict automated/scripted account activity in their ToS. Check the
  terms of any site before pointing this at it, and prefer a site's
  official API where one exists.
- **CAPTCHAs are not bypassed.** If a site shows one, the script will
  simply pause on it for a human to solve.
- **Submission requires an explicit opt-in.** By default the browser
  fills the form and stops — you review and click Submit yourself. Only
  set `auto_submit=True` in `app.py`'s call to `auto_apply.run_auto_apply`
  once you've verified the field mapping is correct for a given site,
  and consider whether submitting many applications unattended is
  something the employer/site would welcome.

## Security note on stored data

The User Profile and resume are saved as plain files under `data/` for
this demo's convenience. This is **not** secure storage. For real use,
either keep the profile in `st.session_state` only (never written to
disk), or wire `profile_manager.py` up to an encrypted store / OS
keychain.
