"""
profile_manager.py
-------------------
Handles the "User Profile" data used to pre-fill and auto-apply to job
applications. Fields are generic and cover the info almost any
application form asks for -- nothing here is tied to a specific site.

Storage note:
    For this demo, the profile is persisted to a local JSON file
    (data/user_profile.json) purely for convenience across app reruns.
    This is NOT secure storage -- do not put sensitive data (e.g.
    government ID numbers) in it. For real use, swap `save_profile`/
    `load_profile` to write into an encrypted store or your OS keychain,
    or simply keep the profile in `st.session_state` only (never
    persisted to disk) if you'd rather not write it to a file at all.
"""

import json
import os
from dataclasses import dataclass, asdict, fields

PROFILE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "user_profile.json")


@dataclass
class UserProfile:
    full_name: str = ""
    email: str = ""
    phone_number: str = ""
    linkedin_url: str = ""
    github_url: str = ""
    portfolio_url: str = ""
    current_degree: str = ""       # e.g. "B.Tech Computer Science, 3rd Year"
    graduation_year: int = 0
    cpi: float = 0.0

    def is_complete(self) -> bool:
        """A lightweight completeness check used to warn users before auto-apply."""
        required = [self.full_name, self.email, self.phone_number]
        return all(str(v).strip() for v in required)


def load_profile() -> UserProfile:
    """Load a saved profile from disk, or return a blank one if none exists."""
    if not os.path.exists(PROFILE_PATH):
        return UserProfile()

    try:
        with open(PROFILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        valid_keys = {f.name for f in fields(UserProfile)}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return UserProfile(**filtered)
    except (json.JSONDecodeError, OSError):
        return UserProfile()


def save_profile(profile: UserProfile) -> None:
    """Persist the profile to disk as JSON."""
    os.makedirs(os.path.dirname(PROFILE_PATH), exist_ok=True)
    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(asdict(profile), f, indent=2)


def profile_to_form_values(profile: UserProfile) -> dict:
    """
    Maps profile fields to a flat dict of *likely* form-field labels/keys
    that job application forms commonly use. This mapping is what
    auto_apply.py uses to match against fields it discovers on a live
    page -- it is intentionally broad/fuzzy rather than site-specific.
    """
    return {
        "full_name": profile.full_name,
        "name": profile.full_name,
        "first_name": profile.full_name.split(" ")[0] if profile.full_name else "",
        "last_name": " ".join(profile.full_name.split(" ")[1:]) if profile.full_name else "",
        "email": profile.email,
        "email_address": profile.email,
        "phone": profile.phone_number,
        "phone_number": profile.phone_number,
        "mobile": profile.phone_number,
        "linkedin": profile.linkedin_url,
        "linkedin_url": profile.linkedin_url,
        "github": profile.github_url,
        "github_url": profile.github_url,
        "portfolio": profile.portfolio_url,
        "website": profile.portfolio_url,
        "degree": profile.current_degree,
        "education": profile.current_degree,
        "graduation_year": str(profile.graduation_year) if profile.graduation_year else "",
        "cpi": str(profile.cpi) if profile.cpi else "",
        "gpa": str(profile.cpi) if profile.cpi else "",
        "cgpa": str(profile.cpi) if profile.cpi else "",
    }
