"""
URL tracking store for managing seen/excluded URLs across refresh cycles.
"""
import json
import os
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")

TRACKING_KEYS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "gclid", "fbclid", "mc_cid", "mc_eid", "mkt_tok"
}

GLOBAL_SECTION = "all"


def ensure_data_dir():
    """Create data directory if it doesn't exist."""
    os.makedirs(DATA_DIR, exist_ok=True)


def normalize_url(url: str) -> str:
    """
    Normalize a URL for comparison by:
    - Lowercasing scheme and netloc
    - Removing tracking parameters (utm_*, gclid, fbclid, etc.)
    - Removing fragments
    """
    if not url:
        return ""
    try:
        p = urlparse(url.strip())
        scheme = (p.scheme or "https").lower()
        netloc = p.netloc.lower()
        path = p.path or "/"
        q = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
             if k.lower() not in TRACKING_KEYS]
        query = urlencode(q, doseq=True)
        return urlunparse((scheme, netloc, path, p.params, query, ""))  # drop fragment
    except Exception:
        return url.strip()


def _file_for(section: str) -> str:
    """Get the path to the seen URLs file for a section."""
    ensure_data_dir()
    safe = "".join(c for c in section.lower() if c.isalnum() or c in ("_", "-"))
    return os.path.join(DATA_DIR, f"seen_{safe}.json")


def load_seen(section: str) -> list:
    """
    Load previously seen URLs for a section, returning normalized URLs.

    Args:
        section: The section identifier (e.g., 'news', 'tips', 'trends', 'all')

    Returns:
        List of normalized URL strings
    """
    path = _file_for(section)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        return [normalize_url(str(x)) for x in data if x]
    except Exception:
        return []


def save_seen(section: str, urls: list) -> None:
    """
    Save seen URLs for a section, storing only normalized unique URLs.

    Args:
        section: The section identifier (e.g., 'news', 'tips', 'trends', 'all')
        urls: List of URLs to save (will be normalized and deduplicated)
    """
    path = _file_for(section)
    uniq = []
    seen = set()
    for u in urls:
        nu = normalize_url(str(u))
        if nu and nu not in seen:
            uniq.append(nu)
            seen.add(nu)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(uniq, f, ensure_ascii=False, indent=2)


def append_seen(section: str, new_urls: list) -> None:
    """
    Append new URLs to the seen list for a section.

    Args:
        section: The section identifier
        new_urls: List of new URLs to add
    """
    prev = load_seen(section)
    save_seen(section, [*new_urls, *prev])
