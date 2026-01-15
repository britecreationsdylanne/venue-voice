"""
URL tracking utilities for managing seen/excluded URLs across refresh cycles.
"""
import os
import json
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode


def normalize_url(url: str) -> str:
    """
    Normalize a URL for comparison by:
    - Lowercasing scheme and netloc
    - Removing tracking parameters (utm_*, gclid, fbclid, etc.)
    - Removing fragments
    """
    if not url:
        return url
    try:
        p = urlparse(url.strip())
        scheme = (p.scheme or "https").lower()
        netloc = p.netloc.lower()
        path = p.path or "/"

        # Remove common tracking parameters
        tracking_keys = {
            "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
            "gclid", "fbclid", "mc_cid", "mc_eid", "mkt_tok"
        }
        q = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
             if k.lower() not in tracking_keys]
        query = urlencode(q, doseq=True)

        return urlunparse((scheme, netloc, path, p.params, query, ""))
    except:
        return url.strip()


def seen_file_path(section_key: str) -> str:
    """Get the path to the seen URLs file for a given section."""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, f'seen_{section_key}.json')


def load_seen_urls(section_key: str) -> list:
    """
    Load previously seen URLs for a section, returning normalized URLs.

    Args:
        section_key: The section identifier (e.g., 'news', 'tips', 'trends', 'all')

    Returns:
        List of normalized URL strings
    """
    path = seen_file_path(section_key)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        # Normalize defensively
        return [normalize_url(str(x)) for x in data if x]
    except Exception:
        return []


def save_seen_urls(section_key: str, urls: list) -> None:
    """
    Save seen URLs for a section, storing only normalized unique URLs.

    Args:
        section_key: The section identifier (e.g., 'news', 'tips', 'trends', 'all')
        urls: List of URLs to save (will be normalized and deduplicated)
    """
    path = seen_file_path(section_key)
    uniq = []
    seen = set()
    for u in urls:
        nu = normalize_url(str(u))
        if nu and nu not in seen:
            uniq.append(nu)
            seen.add(nu)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(uniq, f, ensure_ascii=False, indent=2)
