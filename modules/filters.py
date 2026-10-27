"""
filters.py
----------
Applies the "Universal Search & Eligibility Filters" (spec section 5) to
the jobs DataFrame. Every filter here is generic/dynamic -- there is no
hardcoded skill list. Skills are matched by simple substring search
against whatever the user typed into the "custom skills" box, layered on
top of (not replacing) the AI resume-match score.
"""

import pandas as pd


def apply_filters(
    df: pd.DataFrame,
    countries: list[str],
    custom_skills: list[str],
    opportunity_types: list[str],
    ppo_only: bool,
    min_compensation: int,
    target_grad_year: int,
    min_cpi_user: float,
) -> pd.DataFrame:
    """
    Returns a filtered copy of df based on all active criteria.
    Any filter left empty/default is treated as "no restriction".
    """
    filtered = df.copy()

    # --- Country filter (dynamic free text, matched case-insensitively) ---
    if countries:
        pattern = "|".join(c.strip() for c in countries if c.strip())
        if pattern:
            filtered = filtered[
                filtered["country"].str.contains(pattern, case=False, na=False)
            ]

    # --- Custom skills overlay: keep jobs mentioning ANY typed skill -------
    if custom_skills:
        skill_terms = [s.strip() for s in custom_skills if s.strip()]
        if skill_terms:
            combined_text = (
                filtered["title"].fillna("")
                + " "
                + filtered["description"].fillna("")
                + " "
                + filtered["requirements"].fillna("")
            ).str.lower()
            mask = combined_text.apply(
                lambda text: any(term.lower() in text for term in skill_terms)
            )
            filtered = filtered[mask]

    # --- Opportunity type: Fresher/Entry-Level vs Experienced -------------
    if opportunity_types:
        filtered = filtered[filtered["job_type"].isin(opportunity_types)]

    # --- PPO toggle ---------------------------------------------------------
    if ppo_only:
        filtered = filtered[filtered["has_ppo"] == True]  # noqa: E712

    # --- Minimum compensation ----------------------------------------------
    if min_compensation and min_compensation > 0:
        filtered = filtered[filtered["compensation"] >= min_compensation]

    # --- Target graduation year (exact match against employer's target) ---
    # A job whose grad_year_required is 0 means "not specified" (common with
    # real-API listings that don't label a target class year) -- treat that
    # as open to any year rather than excluding it.
    if target_grad_year and target_grad_year > 0:
        filtered = filtered[
            (filtered["grad_year_required"] == target_grad_year)
            | (filtered["grad_year_required"] == 0)
        ]

    # --- Minimum CPI cutoff: keep jobs the user is ELIGIBLE for -------------
    # (i.e. the job's required cutoff is at or below the user's own CPI)
    if min_cpi_user and min_cpi_user > 0:
        filtered = filtered[filtered["min_cpi_required"] <= min_cpi_user]

    return filtered
