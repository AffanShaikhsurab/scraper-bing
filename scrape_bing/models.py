from dataclasses import dataclass
from typing import Optional

@dataclass
class SearchResult:
    title: str
    url: str
    description: Optional[str] = None



