"""Optional authenticated market-data adapters."""

from datetime import datetime, timedelta
import json
import os
from typing import Any, Dict, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class AlpacaQuoteService:
    """Fetch real US-stock NBBO quotes; credentials are read from the environment."""

    BASE_URL = "https://data.alpaca.markets/v2/stocks/{symbol}/quotes/latest"

    def __init__(self, feed: str = "iex", cache_seconds: int = 30):
        self.key_id = os.getenv("ALPACA_API_KEY_ID") or os.getenv("APCA_API_KEY_ID", "")
        self.secret = os.getenv("ALPACA_API_SECRET_KEY") or os.getenv("APCA_API_SECRET_KEY", "")
        self.feed = feed
        self.cache_seconds = cache_seconds
        self.cache: Dict[str, tuple] = {}
        self.last_error = ""

    @property
    def configured(self) -> bool:
        return bool(self.key_id and self.secret)

    def latest_quote(self, symbol: str, timeout: float = 2.0) -> Optional[Dict[str, Any]]:
        if not self.configured:
            return None
        cached = self.cache.get(symbol)
        if cached and datetime.now() - cached[0] < timedelta(seconds=self.cache_seconds):
            return dict(cached[1])
        try:
            url = self.BASE_URL.format(symbol=symbol) + "?" + urlencode({"feed": self.feed})
            request = Request(url, headers={
                "APCA-API-KEY-ID": self.key_id,
                "APCA-API-SECRET-KEY": self.secret,
                "User-Agent": "InvestmentSimulator/1.0",
            })
            with urlopen(request, timeout=timeout) as response:
                quote = json.loads(response.read().decode("utf-8"))["quote"]
            normalized = {
                "bid_price": float(quote["bp"]), "ask_price": float(quote["ap"]),
                "bid_size": int(quote.get("bs", 0)) * 100,
                "ask_size": int(quote.get("as", 0)) * 100,
                "bid_exchange": quote.get("bx", ""), "ask_exchange": quote.get("ax", ""),
                "timestamp": quote.get("t", ""), "feed": self.feed.upper(),
            }
            if normalized["bid_price"] <= 0 or normalized["ask_price"] <= normalized["bid_price"]:
                raise ValueError("provider returned an invalid or crossed quote")
            self.cache[symbol] = (datetime.now(), normalized)
            self.last_error = ""
            return dict(normalized)
        except Exception as exc:
            self.last_error = str(exc)
            return None
