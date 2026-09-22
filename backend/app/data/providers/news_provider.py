import logging
import hashlib
from datetime import datetime, timezone
import httpx
from app.config.settings import Settings
from app.schemas.news import (
    NewsItem,
    NewsCategory,
    NewsDirection,
    NewsImportance,
    IvImpact,
)

logger = logging.getLogger(__name__)


def classify_category(text: str) -> NewsCategory:
    text_lower = text.lower()
    if "rbi" in text_lower or "repo rate" in text_lower or "monetary policy" in text_lower:
        return "RBI"
    if "fed" in text_lower or "fomc" in text_lower or "powell" in text_lower or "treasury" in text_lower:
        return "Fed"
    if "cpi" in text_lower or "inflation" in text_lower or "wpi" in text_lower:
        return "CPI"
    if "sebi" in text_lower or "regulation" in text_lower or "derivative" in text_lower:
        return "SEBI"
    if "fii" in text_lower or "dii" in text_lower or "inflow" in text_lower or "outflow" in text_lower:
        return "FII_DII"
    if "budget" in text_lower or "tax" in text_lower or "fm" in text_lower:
        return "Budget"
    if "earning" in text_lower or "profit" in text_lower or "quarter" in text_lower or "q1" in text_lower or "q2" in text_lower or "q3" in text_lower or "q4" in text_lower:
        return "Earnings"
    if "crude" in text_lower or "oil" in text_lower or "rupee" in text_lower or "inr" in text_lower:
        return "Crude_INR"
    return "Geopolitical"


def classify_direction(text: str) -> NewsDirection:
    text_lower = text.lower()
    pos_words = ["surge", "jump", "rally", "gain", "bullish", "profit", "growth", "high", "boost", "optimism", "cut"]
    neg_words = ["fall", "drop", "slump", "bearish", "loss", "plunge", "decline", "warn", "risk", "hike", "fear", "inflation"]
    pos_count = sum(1 for w in pos_words if w in text_lower)
    neg_count = sum(1 for w in neg_words if w in text_lower)

    if pos_count > neg_count and pos_count > 0:
        return "Positive"
    elif neg_count > pos_count and neg_count > 0:
        return "Negative"
    elif pos_count > 0 and neg_count > 0:
        return "Mixed"
    return "Neutral"


def classify_importance(text: str) -> NewsImportance:
    text_lower = text.lower()
    if any(k in text_lower for k in ["rbi", "fed", "rate cut", "rate hike", "cpi", "war", "crisis", "sebi"]):
        return "CRITICAL"
    if any(k in text_lower for k in ["earnings", "fii", "surge", "plunge"]):
        return "HIGH"
    return "MEDIUM"


def classify_iv_impact(direction: NewsDirection, importance: NewsImportance) -> IvImpact:
    if importance == "CRITICAL":
        return "Rising" if direction in ["Negative", "Mixed"] else "Crush"
    if direction == "Positive":
        return "Crush"
    if direction == "Negative":
        return "Rising"
    return "Unchanged"


class NewsProvider:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.api_key = settings.news_api_key
        self.base_url = "https://newsapi.org/v2/everything"

    async def fetch_live_news(self, query: str = "NIFTY OR Sensex OR RBI OR Indian stock market", limit: int = 10) -> list[NewsItem]:
        if not self.api_key:
            logger.warning("NewsProvider: NEWS_API_KEY missing, cannot fetch live news.")
            return []

        headers = {"User-Agent": "ArthaLens/1.0"}
        params = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": min(limit, 20),
            "apiKey": self.api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.base_url, headers=headers, params=params)
                if response.status_code != 200:
                    logger.error("NewsAPI request failed with status code %s: %s", response.status_code, response.text)
                    return []
                
                data = response.json()
                if data.get("status") != "ok":
                    logger.error("NewsAPI returned non-ok status: %s", data.get("message"))
                    return []

                articles = data.get("articles", [])
                items: list[NewsItem] = []

                for art in articles:
                    title = art.get("title") or ""
                    description = art.get("description") or art.get("content") or ""
                    if not title or title == "[Removed]":
                        continue

                    full_text = f"{title} {description}"
                    art_url = art.get("url") or title
                    news_id = "news-" + hashlib.md5(art_url.encode()).hexdigest()[:8]

                    category = classify_category(full_text)
                    direction = classify_direction(full_text)
                    importance = classify_importance(full_text)
                    iv_impact = classify_iv_impact(direction, importance)

                    pub_str = art.get("publishedAt")
                    pub_dt = datetime.now(timezone.utc)
                    if pub_str:
                        try:
                            pub_dt = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
                        except Exception:
                            pass

                    source_name = art.get("source", {}).get("name") or "NewsAPI"
                    affected_asset = "BANK NIFTY" if "bank" in full_text.lower() or "rbi" in full_text.lower() else "NIFTY"

                    item = NewsItem(
                        id=news_id,
                        headline=title,
                        summary=description[:250] + ("..." if len(description) > 250 else ""),
                        category=category,
                        affected_asset=affected_asset,
                        direction=direction,
                        importance=importance,
                        iv_impact=iv_impact,
                        affected_strikes=[],
                        expected_move_change=75.0 if importance == "CRITICAL" else 30.0,
                        why_it_matters=f"Live feed from {source_name}: potential impact on {affected_asset} implied volatility.",
                        what_to_watch_next=f"Watch {affected_asset} ATM strike reaction and PCR shifts.",
                        confidence="High" if importance in ["CRITICAL", "HIGH"] else "Medium",
                        timestamp=pub_dt,
                        source=source_name,
                    )
                    items.append(item)

                return items

        except Exception as e:
            logger.exception("Error fetching live news from NewsAPI: %s", e)
            return []
