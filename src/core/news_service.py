"""Small, dependency-free RSS reader for live financial headlines."""

from dataclasses import dataclass
from datetime import datetime
from html import unescape
import re
import threading
from typing import List, Optional
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


@dataclass
class NewsArticle:
    title: str
    summary: str
    source: str
    url: str
    published: str = ""


class LiveNewsService:
    """Fetches public RSS feeds without making gameplay depend on connectivity."""

    FEEDS = (
        ("BBC Business", "https://feeds.bbci.co.uk/news/business/rss.xml"),
        ("BBC Technology", "https://feeds.bbci.co.uk/news/technology/rss.xml"),
        ("US Federal Reserve", "https://www.federalreserve.gov/feeds/press_all.xml"),
    )

    def __init__(self):
        self.articles: List[NewsArticle] = []
        self.last_updated: Optional[datetime] = None
        self.error = ""
        self._lock = threading.Lock()

    @staticmethod
    def _clean(value: str) -> str:
        value = re.sub(r"<[^>]+>", " ", value or "")
        return re.sub(r"\s+", " ", unescape(value)).strip()

    def refresh(self, timeout: float = 3.0) -> List[NewsArticle]:
        collected = []
        errors = []
        for source, url in self.FEEDS:
            try:
                request = Request(url, headers={"User-Agent": "InvestmentSimulator/1.0 RSS Reader"})
                with urlopen(request, timeout=timeout) as response:
                    root = ET.fromstring(response.read())
                for item in root.findall(".//item")[:12]:
                    collected.append(NewsArticle(
                        title=self._clean(item.findtext("title")),
                        summary=self._clean(item.findtext("description")),
                        source=source,
                        url=self._clean(item.findtext("link")),
                        published=self._clean(item.findtext("pubDate")),
                    ))
            except Exception as exc:
                errors.append(f"{source}: {exc}")
        with self._lock:
            if collected:
                self.articles = collected
                self.last_updated = datetime.now()
            self.error = "; ".join(errors)
            return list(self.articles)

    def refresh_async(self):
        """Refresh without freezing Pygame's event loop."""
        threading.Thread(target=self.refresh, name="live-news", daemon=True).start()

    def snapshot(self) -> List[NewsArticle]:
        with self._lock:
            return list(self.articles)
