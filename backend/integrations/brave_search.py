"""
Brave Search API Client
Free tier: 2,000 queries per month
"""

import os
import requests
from typing import List, Dict


class BraveSearchClient:
    """Client for Brave Search API"""

    def __init__(self, api_key: str = None):
        """Initialize Brave Search client"""
        self.api_key = api_key or os.getenv('BRAVE_SEARCH_API_KEY')
        if not self.api_key:
            raise ValueError("BRAVE_SEARCH_API_KEY not found in environment")

        self.base_url = "https://api.search.brave.com/res/v1/web/search"

    def search(
        self,
        query: str,
        count: int = 5,
        freshness: str = "py"  # Past year
    ) -> List[Dict]:
        """
        Search the web using Brave Search

        Args:
            query: Search query
            count: Number of results (max 20)
            freshness: Time filter - "pd" (day), "pw" (week), "pm" (month), "py" (year)

        Returns:
            List of search results with title, description, url
        """
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key
        }

        params = {
            "q": query,
            "count": count,
            "freshness": freshness,
            "text_decorations": False,
            "search_lang": "en"
        }

        try:
            response = requests.get(
                self.base_url,
                headers=headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()

            # Extract web results
            results = []
            web_results = data.get("web", {}).get("results", [])

            for result in web_results:
                results.append({
                    "title": result.get("title", ""),
                    "description": result.get("description", ""),
                    "url": result.get("url", ""),
                    "age": result.get("age", "")
                })

            return results

        except requests.exceptions.RequestException as e:
            print(f"Brave Search API error: {e}")
            return []

    def search_wedding_news(self, month: str) -> List[Dict]:
        """Search for wedding venue industry news - returns 15 results"""
        query = f"wedding venue industry news statistics data 2025 2026 {month}"
        return self.search(query, count=15, freshness="pm")  # Past month, 15 results

    def search_wedding_tips(self, month: str) -> List[Dict]:
        """Search for wedding venue management tips - returns 15 results"""
        query = f"wedding venue marketing tips advice 2025 2026 {month}"
        return self.search(query, count=15, freshness="pm")  # 15 results

    def search_wedding_trends(self, month: str, season: str) -> List[Dict]:
        """Search for seasonal wedding trends - returns 15 results"""
        query = f"wedding trends {season} 2025 2026 venue {month}"
        return self.search(query, count=15, freshness="pm")  # 15 results
