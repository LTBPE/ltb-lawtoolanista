"""
Content extraction and cleaning using Trafilatura.
"""

import logging
import re

logger = logging.getLogger(__name__)

# Regex patterns for noise to remove from extracted text
_NOISE_PATTERNS: list[re.Pattern] = [
    # "Last updated: ..." / "Last modified: ..."
    re.compile(
        r"(?mi)^.*last\s+(?:updated|modified|reviewed|changed)[:\s]+\w+.*$\n?"
    ),
    # "Page last reviewed on ..."
    re.compile(
        r"(?mi)^.*page\s+last\s+reviewed\s+on\s+.*$\n?"
    ),
    # Cookie consent banners
    re.compile(
        r"(?mi)^.*(?:we\s+use\s+cookies|cookie\s+policy|accept\s+cookies|"
        r"by\s+continuing\s+to\s+use\s+this\s+site).*$\n?",
        re.IGNORECASE,
    ),
    # Social share counts e.g. "Share 123 likes"
    re.compile(
        r"(?mi)^.*\bshare\b.*\b\d+\s+(?:likes?|shares?|tweets?)\b.*$\n?",
        re.IGNORECASE,
    ),
    # Navigation breadcrumbs: "Home > Courts > Rules"
    re.compile(
        r"(?mi)^(?:[\w\s]+\s*[>|/]\s*){2,}[\w\s]+$\n?"
    ),
    # "Print this page" / "Email this page"
    re.compile(
        r"(?mi)^.*\b(?:print|email)\s+this\s+page\b.*$\n?",
        re.IGNORECASE,
    ),
    # Skip navigation links
    re.compile(
        r"(?mi)^.*\bskip\s+(?:to\s+)?(?:main\s+content|navigation|nav)\b.*$\n?",
        re.IGNORECASE,
    ),
]

# Normalise runs of 3+ blank lines into 2
_EXTRA_BLANK_LINES = re.compile(r"\n{3,}")


def extract_and_clean(html: str, url: str) -> str:
    """
    Extract main text content from HTML and remove noise.

    Args:
        html: Raw HTML string.
        url: Source URL (used by trafilatura for metadata hints).

    Returns:
        Cleaned plain-text string, or empty string if extraction failed.
    """
    if not html or not html.strip():
        return ""

    try:
        import trafilatura

        text = trafilatura.extract(
            html,
            url=url,
            include_tables=True,
            favor_recall=True,
            no_fallback=False,
            include_comments=False,
            include_formatting=False,
        )
    except Exception as exc:
        logger.warning("Trafilatura extraction failed for %s: %s", url, exc)
        text = None

    if not text:
        # Fallback: strip all HTML tags and return raw text
        text = re.sub(r"<[^>]+>", " ", html)

    # Apply noise filters
    for pattern in _NOISE_PATTERNS:
        text = pattern.sub("", text)

    # Normalise whitespace
    # Replace tabs with spaces
    text = text.replace("\t", " ")
    # Collapse multiple spaces to one
    text = re.sub(r" {2,}", " ", text)
    # Strip trailing spaces from each line
    text = "\n".join(line.rstrip() for line in text.splitlines())
    # Collapse 3+ blank lines to 2
    text = _EXTRA_BLANK_LINES.sub("\n\n", text)
    text = text.strip()

    return text
