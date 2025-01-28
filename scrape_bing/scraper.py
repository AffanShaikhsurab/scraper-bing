
from urllib.parse import urlencode, urlunparse
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup


from urllib.parse import urlunparse, urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from bs4 import BeautifulSoup
from typing import List, Optional, Dict
import re
from dataclasses import dataclass
import time
from random import choice

from .models import SearchResult


class BingScraper:
    # List of common user agents for rotation
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    ]

    def __init__(self, max_retries: int = 3, delay_between_requests: float = 1.0):
        self.max_retries = max_retries
        self.delay_between_requests = delay_between_requests
        self.last_request_time = 0

    def _get_random_user_agent(self) -> str:
        """Return a random user agent from the list."""
        return choice(self.USER_AGENTS)

    def _enforce_rate_limit(self):
        """Ensure minimum delay between requests."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.delay_between_requests:
            time.sleep(self.delay_between_requests - time_since_last_request)
        self.last_request_time = time.time()

    def _clean_url(self, url: str) -> Optional[str]:
        """Clean and validate URLs."""
        if not url:
            return None
            
        # Remove Bing redirect URLs
        if url.startswith("/"):
            return None
        if "bing.com" in url.lower():
            return None
            
        # Remove tracking parameters
        url = re.sub(r'utm_[^&]*&?', '', url)
        url = re.sub(r'[?&]$', '', url)
        
        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            return None
            
        return url

    def _extract_search_results(self, soup: BeautifulSoup) -> List[SearchResult]:
        """Extract search results from the BeautifulSoup object."""
        results = []
        
        # Find main search results
        search_results = soup.find_all('li', class_='b_algo')
        
        for result in search_results:
            # Extract title and URL
            title_elem = result.find('h2')
            if not title_elem or not title_elem.find('a'):
                continue
                
            title = title_elem.get_text().strip()
            url = title_elem.find('a').get('href')
            
            # Clean URL
            clean_url = self._clean_url(url)
            if not clean_url:
                continue
                
            # Extract description
            desc_elem = result.find('p')
            description = desc_elem.get_text().strip() if desc_elem else None
            
            results.append(SearchResult(
                title=title,
                url=clean_url,
                description=description
            ))
            
        return results

    def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """
        Perform a Bing search and return results.
        
        Args:
            query: Search query string
            num_results: Maximum number of results to return
            
        Returns:
            List of SearchResult objects
            
        Raises:
            ValueError: If query is empty
            ConnectionError: If network connection fails
            RuntimeError: If parsing fails
        """
        if not query.strip():
            raise ValueError("Search query cannot be empty")
            
        self._enforce_rate_limit()
        
        # Construct search URL
        url = urlunparse((
            "https",
            "www.bing.com",
            "/search",
            "",
            urlencode({"q": query, "n": num_results}),
            ""
        ))
        
        # Initialize variables for retry loop
        attempts = 0
        while attempts < self.max_retries:
            try:
                # Create request with random user agent
                headers = {"User-Agent": self._get_random_user_agent()}
                req = Request(url, headers=headers)
                
                # Make request
                with urlopen(req) as response:
                    html = response.read()
                    
                # Parse response
                soup = BeautifulSoup(html, 'html.parser')
                results = self._extract_search_results(soup)
                
                # Limit results to requested number
                return results[:num_results]
                
            except HTTPError as e:
                attempts += 1
                if attempts == self.max_retries:
                    raise ConnectionError(f"HTTP Error after {self.max_retries} attempts: {e.code} {e.reason}")
                time.sleep(self.delay_between_requests * attempts)
                
            except URLError as e:
                raise ConnectionError(f"Network error: {str(e)}")
                
            except Exception as e:
                raise RuntimeError(f"Error parsing search results: {str(e)}")


