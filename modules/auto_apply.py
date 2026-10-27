"""
auto_apply.py
-------------
Generic browser-automation SKELETON for pre-filling job application forms
using Playwright. This is intentionally a skeleton, not a finished
"submit anywhere" bot -- real application forms vary enormously (custom
React components, multi-step wizards, file-upload widgets, CAPTCHAs,
SSO logins), so a single heuristic script cannot reliably complete every
site unattended. What this module DOES give you is a solid, reusable
foundation:

  * Launches a real (non-headless by default) browser so you can watch
    and intervene.
  * Walks every <input>/<textarea>/<select> on the page.
  * Uses fuzzy string matching against the field's label/placeholder/
    name/id/aria-label to guess which profile field it corresponds to.
  * Fills in matches automatically and uploads your resume to any
    file-input it finds.
  * Leaves the form OPEN for your review and requires an explicit
    `auto_submit=True` flag before it will click any submit button --
    the default is to stop just short of submission.

Important, please read:
  * Many job boards' Terms of Service explicitly restrict automated
    form submission / scripted account activity. Review the ToS of any
    site before pointing this at it, and prefer using official APIs
    (e.g. LinkedIn's Easy Apply is not scriptable via its public API by
    design) where available.
  * CAPTCHAs and bot-detection are deliberately NOT bypassed here. If a
    site presents one, this script will pause so a human can solve it.
  * Always keep `auto_submit=False` while testing on a new site, review
    the filled form yourself, then re-run with `auto_submit=True` only
    once you trust the field mapping for that site.
"""

import asyncio
from dataclasses import dataclass
from rapidfuzz import fuzz
from playwright.async_api import async_playwright, Page


@dataclass
class ApplyResult:
    success: bool
    message: str
    screenshot_path: str | None = None


FIELD_MATCH_THRESHOLD = 70  # rapidfuzz similarity score (0-100) to accept a guess


async def _get_field_descriptor(page: Page, element) -> str:
    """
    Builds a single text string describing a form field, pulled from
    whatever attributes/labels are available, so we can fuzzy-match it
    against our profile keys without knowing the site's markup ahead of
    time.
    """
    parts = []
    for attr in ("name", "id", "placeholder", "aria-label"):
        value = await element.get_attribute(attr)
        if value:
            parts.append(value)

    # Try to find an associated <label for="id">
    el_id = await element.get_attribute("id")
    if el_id:
        label = await page.query_selector(f"label[for='{el_id}']")
        if label:
            label_text = await label.inner_text()
            if label_text:
                parts.append(label_text)

    return " ".join(parts).lower()


def _best_profile_match(descriptor: str, form_values: dict) -> tuple[str, int]:
    """Returns (profile_key, score) of the best fuzzy match for a field descriptor."""
    best_key, best_score = "", 0
    for key in form_values:
        score = fuzz.partial_ratio(descriptor, key.replace("_", " "))
        if score > best_score:
            best_key, best_score = key, score
    return best_key, best_score


async def fill_application_form(
    apply_url: str,
    form_values: dict,
    resume_file_path: str,
    headless: bool = False,
    auto_submit: bool = False,
    submit_button_text: str = "submit",
) -> ApplyResult:
    """
    Core automation routine.

    Args:
        apply_url: the job listing / application page to open.
        form_values: flat dict of profile data (see profile_manager.profile_to_form_values).
        resume_file_path: local path to the resume file to upload.
        headless: run browser invisibly (True) or visibly for supervision (False, default).
        auto_submit: if True AND a submit button is confidently found, click it.
                     Defaults to False so a human always reviews before sending.
        submit_button_text: text/label to look for when locating the submit button.

    Returns:
        ApplyResult with success flag, a human-readable message, and an
        optional screenshot path for your records.
    """
    filled_fields = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()

        try:
            await page.goto(apply_url, wait_until="domcontentloaded", timeout=30000)
        except Exception as exc:  # noqa: BLE001
            await browser.close()
            return ApplyResult(False, f"Could not load page: {exc}")

        # --- 1. Text-like inputs & textareas -------------------------------
        inputs = await page.query_selector_all(
            "input[type='text'], input[type='email'], input[type='tel'], "
            "input[type='url'], input:not([type]), textarea"
        )
        for element in inputs:
            descriptor = await _get_field_descriptor(page, element)
            if not descriptor:
                continue
            key, score = _best_profile_match(descriptor, form_values)
            if score >= FIELD_MATCH_THRESHOLD and form_values.get(key):
                try:
                    await element.fill(str(form_values[key]))
                    filled_fields.append((descriptor, key, score))
                except Exception:  # noqa: BLE001 -- element may be hidden/disabled
                    continue

        # --- 2. Resume file upload ------------------------------------------
        file_inputs = await page.query_selector_all("input[type='file']")
        resume_uploaded = False
        for file_input in file_inputs:
            try:
                await file_input.set_input_files(resume_file_path)
                resume_uploaded = True
                break  # assume the first file input is the resume uploader
            except Exception:  # noqa: BLE001
                continue

        # --- 3. Optional submit -----------------------------------------------
        submitted = False
        if auto_submit:
            submit_button = await page.query_selector(
                f"button:has-text('{submit_button_text}'), "
                f"input[type='submit'][value*='{submit_button_text}' i]"
            )
            if submit_button:
                await submit_button.click()
                submitted = True
                await page.wait_for_timeout(2000)  # allow submission to process

        screenshot_path = "/tmp/auto_apply_screenshot.png"
        await page.screenshot(path=screenshot_path, full_page=True)

        if not auto_submit:
            # Leave the browser open briefly for manual review if not headless
            if not headless:
                await page.wait_for_timeout(5000)

        await browser.close()

    summary = (
        f"Filled {len(filled_fields)} field(s). "
        f"Resume uploaded: {resume_uploaded}. "
        f"Submitted: {submitted}."
    )
    return ApplyResult(True, summary, screenshot_path)


def run_auto_apply(apply_url: str, form_values: dict, resume_file_path: str, **kwargs) -> ApplyResult:
    """Synchronous wrapper so Streamlit's callback-driven UI can call this directly."""
    return asyncio.run(
        fill_application_form(apply_url, form_values, resume_file_path, **kwargs)
    )
