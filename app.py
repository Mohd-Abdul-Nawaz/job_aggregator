"""
app.py
------
Universal Job & Internship Aggregator -- main Streamlit entry point.

Run with:
    streamlit run app.py

Architecture:
    modules/resume_parser.py    -> PDF/DOCX text extraction
    modules/matching_engine.py  -> resume-vs-job scoring (local TF-IDF or LLM)
    modules/mock_data.py        -> demo dataset (swap for a real scraper later)
    modules/filters.py          -> eligibility/search filtering
    modules/profile_manager.py  -> user profile CRUD
    modules/auto_apply.py       -> Playwright auto-fill skeleton

Nothing in this file (or the modules it imports) hardcodes a specific
skill set or a specific job-board website -- the resume, the skills
typed into the sidebar, and the job dataset are all supplied at runtime.
"""

import os
import streamlit as st
import pandas as pd

from modules import resume_parser, matching_engine, mock_data, live_data, filters, profile_manager, auto_apply

st.set_page_config(page_title="Job & Internship Aggregator", layout="wide")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
RESUME_STORE_PATH = os.path.join(DATA_DIR, "uploaded_resume")
os.makedirs(DATA_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------
if "jobs_df" not in st.session_state:
    st.session_state.jobs_df = mock_data.get_mock_jobs()

if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""

if "resume_file_path" not in st.session_state:
    st.session_state.resume_file_path = ""

if "profile" not in st.session_state:
    st.session_state.profile = profile_manager.load_profile()

if "use_llm_matching" not in st.session_state:
    st.session_state.use_llm_matching = False


# ---------------------------------------------------------------------------
# SIDEBAR: Resume upload + Universal filters (spec sections 1 & 5)
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("📄 Resume")
    uploaded_resume = st.file_uploader(
        "Upload your resume (PDF or DOCX)", type=["pdf", "docx"]
    )

    if uploaded_resume is not None:
        try:
            # Save a persistent copy to disk -- auto_apply needs a real file path
            # to hand to Playwright's file-upload input, not just in-memory bytes.
            file_ext = os.path.splitext(uploaded_resume.name)[1]
            saved_path = RESUME_STORE_PATH + file_ext
            file_bytes = uploaded_resume.getvalue()
            with open(saved_path, "wb") as f:
                f.write(file_bytes)

            # Re-wrap bytes so resume_parser (which calls .read()) works
            # regardless of Streamlit's internal buffer state.
            import io
            wrapper = io.BytesIO(file_bytes)
            wrapper.name = uploaded_resume.name
            st.session_state.resume_text = resume_parser.parse_resume(wrapper)
            st.session_state.resume_file_path = saved_path
            st.success(f"Resume parsed ✅ ({len(st.session_state.resume_text)} characters extracted)")
        except ValueError as e:
            st.error(str(e))

    st.session_state.use_llm_matching = st.toggle(
        "Use LLM for smarter matching (requires LLM_API_KEY env var)",
        value=st.session_state.use_llm_matching,
        help="If off, matching uses fast local TF-IDF text similarity instead.",
    )

    st.divider()
    st.header("🌐 Data Source")
    st.caption(
        "The bundled demo dataset uses placeholder links that don't go "
        "anywhere real. Switch to Live Jobs to pull actual, currently-open "
        "listings with working apply links."
    )

    data_source = st.radio(
        "Job listings source",
        options=["Demo / Mock Data", "Live Jobs (Real APIs)"],
        index=0,
    )

    if data_source == "Live Jobs (Real APIs)":
        live_query = st.text_input(
            "Search keywords", value="software", placeholder="e.g. python developer, data analyst"
        )
        live_sources = st.multiselect(
            "Sources to query",
            options=["RemoteOK", "Arbeitnow", "Adzuna"],
            default=["RemoteOK", "Arbeitnow", "Adzuna"],
        )

        with st.expander("Adzuna API credentials (free signup required)"):
            st.caption(
                "Adzuna needs a free key -- sign up at "
                "https://developer.adzuna.com/ then paste your credentials "
                "below, or set ADZUNA_APP_ID / ADZUNA_APP_KEY as environment "
                "variables instead. RemoteOK and Arbeitnow need no key."
            )
            adzuna_country = st.selectbox(
                "Adzuna country code", options=["in", "us", "gb", "ca", "au", "de"], index=0
            )
            adzuna_app_id = st.text_input("ADZUNA_APP_ID", value=os.environ.get("ADZUNA_APP_ID", ""))
            adzuna_app_key = st.text_input(
                "ADZUNA_APP_KEY", value=os.environ.get("ADZUNA_APP_KEY", ""), type="password"
            )

        if st.button("🔄 Fetch Live Jobs Now"):
            with st.spinner("Fetching real, currently-open listings..."):
                live_df, warnings = live_data.fetch_all_live_jobs(
                    query=live_query,
                    country_code=adzuna_country,
                    adzuna_app_id=adzuna_app_id,
                    adzuna_app_key=adzuna_app_key,
                    sources=live_sources,
                )
            if not live_df.empty:
                st.session_state.jobs_df = live_df
                st.success(f"Fetched {len(live_df)} real listings. Every apply link below is a live URL.")
            else:
                st.error("No live jobs were fetched -- see warnings below.")
            for w in warnings:
                st.warning(w)

    st.divider()
    st.header("🔎 Search & Eligibility Filters")

    countries_input = st.text_input(
        "Target countries (comma-separated)", placeholder="e.g. India, Remote, USA"
    )
    countries = [c.strip() for c in countries_input.split(",") if c.strip()]

    skills_input = st.text_input(
        "Custom skills to overlay (comma-separated)", placeholder="e.g. React, Python, SQL"
    )
    custom_skills = [s.strip() for s in skills_input.split(",") if s.strip()]

    opportunity_types = st.multiselect(
        "Opportunity type",
        options=["Fresher / Entry-Level", "Experienced"],
        default=[],
    )

    ppo_only = st.checkbox("Internships with Job Offer (PPO) only")

    min_compensation = st.number_input(
        "Minimum compensation (in listing's currency)", min_value=0, value=0, step=1000
    )

    target_grad_year = st.number_input(
        "Target B.Tech graduation year", min_value=0, max_value=2035, value=0, step=1
    )

    min_cpi_user = st.number_input(
        "Your CPI / GPA (used to filter out jobs whose cutoff you don't meet)",
        min_value=0.0, max_value=10.0, value=0.0, step=0.1,
    )


# ---------------------------------------------------------------------------
# MAIN AREA: Tabs for Dashboard and User Profile
# ---------------------------------------------------------------------------
tab_dashboard, tab_profile = st.tabs(["📋 Job Dashboard", "🧑 User Profile"])


# ---------------------------------------------------------------------------
# TAB: User Profile (spec section 3)
# ---------------------------------------------------------------------------
with tab_profile:
    st.subheader("Pre-Filled User Profile")
    st.caption(
        "Stored locally in `data/user_profile.json` for this demo. "
        "For production use, swap this for encrypted storage or keep it "
        "session-only -- see the comment at the top of profile_manager.py."
    )

    profile = st.session_state.profile

    col1, col2 = st.columns(2)
    with col1:
        full_name = st.text_input("Full Name", value=profile.full_name)
        email = st.text_input("Email", value=profile.email)
        phone_number = st.text_input("Phone Number", value=profile.phone_number)
        linkedin_url = st.text_input("LinkedIn URL", value=profile.linkedin_url)
    with col2:
        github_url = st.text_input("GitHub URL", value=profile.github_url)
        portfolio_url = st.text_input("Portfolio URL", value=profile.portfolio_url)
        current_degree = st.text_input(
            "Current Degree (e.g. B.Tech CSE, 3rd Year)", value=profile.current_degree
        )
        col2a, col2b = st.columns(2)
        with col2a:
            graduation_year = st.number_input(
                "Graduation Year", min_value=0, max_value=2035,
                value=profile.graduation_year or 0, step=1,
            )
        with col2b:
            cpi = st.number_input(
                "CPI", min_value=0.0, max_value=10.0, value=profile.cpi or 0.0, step=0.01
            )

    if st.button("💾 Save Profile", type="primary"):
        updated = profile_manager.UserProfile(
            full_name=full_name,
            email=email,
            phone_number=phone_number,
            linkedin_url=linkedin_url,
            github_url=github_url,
            portfolio_url=portfolio_url,
            current_degree=current_degree,
            graduation_year=int(graduation_year),
            cpi=float(cpi),
        )
        profile_manager.save_profile(updated)
        st.session_state.profile = updated
        st.success("Profile saved.")


# ---------------------------------------------------------------------------
# TAB: Job Dashboard (spec sections 1, 2, 4)
# ---------------------------------------------------------------------------
with tab_dashboard:
    st.subheader("Job & Internship Dashboard")

    df = st.session_state.jobs_df.copy()

    # --- Apply eligibility/search filters (section 5) -----------------------
    df = filters.apply_filters(
        df,
        countries=countries,
        custom_skills=custom_skills,
        opportunity_types=opportunity_types,
        ppo_only=ppo_only,
        min_compensation=min_compensation,
        target_grad_year=target_grad_year,
        min_cpi_user=min_cpi_user,
    )

    # --- AI match scoring + ranked sort (section 1) --------------------------
    if st.session_state.resume_text:
        scores, rationales = matching_engine.score_all_jobs(
            st.session_state.resume_text, df, use_llm=st.session_state.use_llm_matching
        )
        df["match_score"] = scores
        df["match_rationale"] = rationales
        df = df.sort_values("match_score", ascending=False).reset_index(drop=True)
    else:
        df["match_score"] = None
        df["match_rationale"] = "Upload a resume in the sidebar to see match scores."
        st.info("👈 Upload a resume in the sidebar to enable AI-ranked sorting.")

    st.caption(f"Showing {len(df)} of {len(st.session_state.jobs_df)} total listings.")

    if df.empty:
        st.warning("No jobs match your current filters. Try loosening them.")

    # --- Render each job as a row with expandable details + apply button ---
    for idx, row in df.iterrows():
        score_label = f"{row['match_score']:.0f}%" if pd.notna(row["match_score"]) else "—"

        header_cols = st.columns([4, 2, 2, 1.5, 1.5])
        header_cols[0].markdown(f"**{row['title']}** — {row['company']}")
        header_cols[1].markdown(f"🌐 *{row['source_site']}*")
        header_cols[2].markdown(f"📍 {row['location']}")
        header_cols[3].markdown(f"🎯 Match: **{score_label}**")
        apply_clicked = header_cols[4].button("🚀 One-Click Apply", key=f"apply_{idx}")

        # --- Expandable requirements/description preview (section 2) -------
        with st.expander("View full details"):
            detail_cols = st.columns(2)
            with detail_cols[0]:
                st.markdown(f"**Company:** {row['company']}")
                st.markdown(f"**Source:** {row['source_site']}")
                st.markdown(f"**Type:** {row['job_type']} | **Internship:** {row['is_internship']}")
                st.markdown(f"**PPO offered:** {row['has_ppo']}")
                st.markdown(
                    f"**Compensation:** {row['compensation']:,} {row['compensation_currency']}"
                )
                st.markdown(f"**Min CPI required:** {row['min_cpi_required']}")
                st.markdown(f"**Target grad year:** {row['grad_year_required']}")
                st.markdown(f"**Posted:** {row['posted_date']}")
                st.markdown(f"**Apply URL:** {row['apply_url']}")
            with detail_cols[1]:
                if row["match_score"] is not None and pd.notna(row["match_score"]):
                    st.markdown(f"**AI Match Rationale:** {row['match_rationale']}")
                st.markdown("**Description**")
                st.write(row["description"])
                st.markdown("**Requirements**")
                st.write(row["requirements"])

        # --- One-Click Auto-Apply pipeline (section 4) --------------------
        if apply_clicked:
            profile = st.session_state.profile
            if not profile.is_complete():
                st.error(
                    "Your User Profile is incomplete. Fill in at least your name, "
                    "email, and phone number in the '🧑 User Profile' tab first."
                )
            elif not st.session_state.resume_file_path:
                st.error("Please upload a resume in the sidebar before applying.")
            else:
                with st.spinner(f"Launching browser to apply to {row['company']}..."):
                    form_values = profile_manager.profile_to_form_values(profile)
                    result = auto_apply.run_auto_apply(
                        apply_url=row["apply_url"],
                        form_values=form_values,
                        resume_file_path=st.session_state.resume_file_path,
                        headless=False,      # visible so you can supervise
                        auto_submit=False,   # NEVER auto-submits without explicit opt-in
                    )
                if result.success:
                    st.success(
                        f"Form pre-filled for {row['company']}. {result.message} "
                        "Review the browser window and submit manually, or re-run "
                        "with auto_submit=True in auto_apply.py once you trust the "
                        "field mapping for this site."
                    )
                    if result.screenshot_path and os.path.exists(result.screenshot_path):
                        st.image(result.screenshot_path, caption="Filled form screenshot")
                else:
                    st.error(f"Auto-apply failed: {result.message}")

        st.divider()
