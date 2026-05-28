"""
Claude AI change analysis via the Anthropic SDK.
"""

import json
import logging
from typing import Any

from shared.config import config

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are an expert in court docketing rules and legal filing procedures. "
    "Analyze website changes to determine if they affect filing requirements, "
    "deadlines, fees, or procedures that attorneys need to update in their "
    "practice management systems."
)

_NOT_ANALYZED_RESULT: dict[str, Any] = {
    "is_relevant": True,
    "summary": "AI analysis not performed. Manual review required.",
    "category": "other",
    "priority": "medium",
    "action_required": "Review change manually to determine impact on docketing rules.",
}


def _build_user_prompt(
    court_name: str,
    url: str,
    old_content: str,
    new_content: str,
    diff_text: str,
) -> str:
    """Build the user prompt for Claude."""
    diff_excerpt = diff_text[:3000] if diff_text else "(no diff available)"
    old_excerpt = old_content[:1000] if old_content else "(not available)"
    new_excerpt = new_content[:1000] if new_content else "(not available)"

    return (
        f"Court: {court_name}\n"
        f"URL: {url}\n\n"
        f"=== DIFF (first 3000 chars) ===\n{diff_excerpt}\n\n"
        f"=== PREVIOUS CONTENT (first 1000 chars) ===\n{old_excerpt}\n\n"
        f"=== NEW CONTENT (first 1000 chars) ===\n{new_excerpt}\n\n"
        "Analyze this change and respond ONLY with a JSON object matching this schema:\n"
        "{\n"
        '  "is_relevant": <bool>,\n'
        '  "summary": "<1-2 sentence description of what changed>",\n'
        '  "category": "<fees|deadlines|format|e-filing|contact|holiday-closure'
        "|new-requirement|removed-requirement|other>\",\n"
        '  "priority": "<high|medium|low>",\n'
        '  "action_required": "<Specific action for docketing staff, or empty string>"\n'
        "}\n\n"
        "is_relevant should be true only if the change affects filing requirements, "
        "deadlines, fees, procedures, or other information that attorneys and docketing "
        "staff would need to update in their practice management systems."
    )


def _parse_ai_response(raw: str) -> dict[str, Any]:
    """Parse and validate the JSON response from Claude."""
    # Strip markdown code fences if present
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        # Remove first and last fence lines
        inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        text = "\n".join(inner).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        logger.warning("Failed to parse AI response as JSON: %s. Raw: %s", exc, raw[:500])
        return _NOT_ANALYZED_RESULT.copy()

    # Validate and normalise fields
    result: dict[str, Any] = {}

    result["is_relevant"] = bool(data.get("is_relevant", True))

    summary = str(data.get("summary", ""))[:1000]
    result["summary"] = summary

    valid_categories = {
        "fees", "deadlines", "format", "e-filing", "contact",
        "holiday-closure", "new-requirement", "removed-requirement", "other",
    }
    category = str(data.get("category", "other")).lower()
    result["category"] = category if category in valid_categories else "other"

    valid_priorities = {"high", "medium", "low"}
    priority = str(data.get("priority", "medium")).lower()
    result["priority"] = priority if priority in valid_priorities else "medium"

    result["action_required"] = str(data.get("action_required", ""))[:1000]

    return result


async def analyze_change(
    court_name: str,
    url: str,
    old_content: str,
    new_content: str,
    diff_text: str,
) -> dict[str, Any]:
    """
    Analyze a content change using Claude Haiku.

    Args:
        court_name: Human-readable court name.
        url: The court URL that changed.
        old_content: Previous page content.
        new_content: New page content.
        diff_text: Unified diff of old vs new.

    Returns:
        Dictionary with keys: is_relevant, summary, category, priority, action_required.
        Falls back to _NOT_ANALYZED_RESULT on error or if AI is disabled.
    """
    if not config.ai_configured:
        logger.info("AI not configured or disabled; skipping analysis for %s", url)
        return _NOT_ANALYZED_RESULT.copy()

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

        user_prompt = _build_user_prompt(
            court_name, url, old_content, new_content, diff_text
        )

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        raw_response = message.content[0].text
        logger.debug("AI raw response for %s: %s", url, raw_response[:300])

        return _parse_ai_response(raw_response)

    except Exception as exc:
        logger.error("AI analysis failed for %s: %s", url, exc)
        return _NOT_ANALYZED_RESULT.copy()
