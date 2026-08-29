import requests
from datetime import datetime, timedelta
import time 
from sqlalchemy.orm import Session
from utils.database import get_db
from utils.models import Announcement
import yfinance as yf
from api.watchlist import NIFTY_50_SYMBOLS
from utils.models import PriceSnapshot
from api.watchlist import WATCHLIST
from transformers import pipeline

IST_OFFSET = timedelta(hours=5, minutes=30)
def parse_bse_datetime(raw_str: str) -> datetime:
    """BSE timestamps are in IST — convert to UTC for consistent storage."""
    ist_time = datetime.strptime(raw_str, "%Y-%m-%dT%H:%M:%S")
    return ist_time - IST_OFFSET


BSE_URL = "https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
    "Referer": "https://www.bseindia.com/",
    "sec-ch-ua": '"Not=A?Brand";v="99", "Google Chrome";v="151", "Chromium";v="151"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}


def fetch_announcements(from_date: str, to_date: str) -> list[dict]:
    params = {
        "pageno": 1,
        "strCat": -1,
        "strPrevDate": from_date,
        "strScrip": "",
        "strSearch": "P",
        "strToDate": to_date,
        "strType": "C",
        "subcategory": -1,
    }
    response = requests.get(BSE_URL, headers=HEADERS, params=params, timeout=15)
    response.raise_for_status()
    return response.json().get("Table", [])

def fetch_announcements_range(start_date: str, end_date: str) -> list[dict]:
    start = datetime.strptime(start_date, "%Y%m%d")
    end = datetime.strptime(end_date, "%Y%m%d")

    all_announcements = []
    current = start

    while current <= end:
        date_str = current.strftime("%Y%m%d")
        announcements = fetch_announcements(date_str, date_str)
        all_announcements.extend(announcements)
        current += timedelta(days=1)
        time.sleep(0.5)

    return all_announcements

def save_announcements(db: Session, announcements: list[dict]) -> int:
    inserted = 0
    watchlist_scrip_codes = set(WATCHLIST.values()) 

    for raw in announcements:
        news_id = raw.get("NEWSID")
        scrip_code = raw.get("SCRIP_CD")
        if not news_id or scrip_code not in watchlist_scrip_codes:
            continue

        exists = db.query(Announcement).filter(Announcement.news_id == news_id).first()
        if exists:
            continue

        try:
            announced_at = parse_bse_datetime(raw["News_submission_dt"])
        except (KeyError, ValueError):
            announced_at = datetime.utcnow()

        record = Announcement(
            news_id=news_id,
            scrip_code=scrip_code,
            company_name=raw.get("SLONGNAME", "Unknown"),
            headline=raw.get("HEADLINE", ""),
            category=raw.get("CATEGORYNAME"),
            subcategory=raw.get("SUBCATNAME"),
            announced_at=announced_at,
            full_text=raw.get("MORE")
        )
        db.add(record)
        inserted += 1

    db.commit()
    return inserted

def fetch_price(symbol: str) -> dict:
    ticker = yf.Ticker(symbol)
    info = ticker.info
    return {
        "symbol": symbol,
        "price": info.get("currentPrice"),
        "change_percent": info.get("regularMarketChangePercent"),
        "volume": info.get("volume"),
    }


def save_price_snapshot(db: Session, price_data: dict) -> PriceSnapshot:
    record = PriceSnapshot(
        symbol=price_data["symbol"],
        price=price_data["price"],
        change_percent=price_data["change_percent"],
        volume=price_data["volume"],
    )
    db.add(record)
    db.commit()
    return record


def ingest_all_prices(db: Session) -> int:
    saved = 0
    for symbol in WATCHLIST.keys():
        try:
            price_data = fetch_price(symbol)
            save_price_snapshot(db, price_data)
            saved += 1
        except Exception as e:
            print(f"Failed to fetch price for {symbol}: {e}")
            continue
    return saved


_sentiment_pipeline = None

def get_sentiment_pipeline():
    """Load the model once, reuse across calls — loading it fresh every time is slow."""
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        _sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="ProsusAI/finbert",
            tokenizer="ProsusAI/finbert",
        )
    return _sentiment_pipeline


def score_sentiment(text: str) -> tuple[str, float]:
    clf = get_sentiment_pipeline()
    result = clf(text[:512])[0]  # FinBERT has a token limit, truncate long headlines
    return result["label"].lower(), float(result["score"])

def score_pending_announcements(db: Session, batch_size: int = 20) -> int:
    pending = (
        db.query(Announcement)
        .filter(Announcement.sentiment_label.is_(None))
        .limit(batch_size)
        .all()
    )

    scored = 0
    for record in pending:
        text_to_score = record.full_text or record.headline
        label, score = score_sentiment(text_to_score)
        record.sentiment_label = label
        record.sentiment_score = score
        record.sentiment_scored_at = datetime.utcnow()
        scored += 1

    db.commit()
    return scored


def get_stock_sentiment_summary(db: Session, scrip_code: int) -> dict:
    records = (
        db.query(Announcement)
        .filter(
            Announcement.scrip_code == scrip_code,
            Announcement.sentiment_label.isnot(None),
        )
        .all()
    )

    if not records:
        return {"scrip_code": scrip_code, "message": "No scored announcements found"}

    total = len(records)
    positive = sum(1 for r in records if r.sentiment_label == "positive")
    negative = sum(1 for r in records if r.sentiment_label == "negative")
    neutral = total - positive - negative

    latest = max(records, key=lambda r: r.announced_at)

    return {
        "scrip_code": scrip_code,
        "company_name": latest.company_name,
        "total_announcements": total,
        "positive": positive,
        "negative": negative,
        "neutral": neutral,
        "net_sentiment": round((positive - negative) / total, 3),
        "latest_announcement_at": latest.announced_at,
    }

def get_stock_announcements(db: Session, scrip_code: int, limit: int = 20) -> list:
    return (
        db.query(Announcement)
        .filter(Announcement.scrip_code == scrip_code)
        .order_by(Announcement.announced_at.desc())
        .limit(limit)
        .all()
    )

def get_market_alerts(db: Session, min_announcements: int = 2, threshold: float = 0.3) -> list:
    alerts = []

    for symbol, scrip_code in WATCHLIST.items():
        summary = get_stock_sentiment_summary(db, scrip_code)

        if "message" in summary:
            continue


        if summary["total_announcements"] < min_announcements:
            continue
        if abs(summary["net_sentiment"]) < threshold:
            continue

        alerts.append({
            "symbol": symbol,
            **summary,
        })

    alerts.sort(key=lambda a: abs(a["net_sentiment"]), reverse=True)

    return alerts


SCRIP_CODE_TO_SYMBOL = {v: k for k, v in WATCHLIST.items()}

def get_composite_signal(db: Session, scrip_code: int) -> dict:
    symbol = SCRIP_CODE_TO_SYMBOL.get(scrip_code)
    if not symbol:
        return {"scrip_code": scrip_code, "message": "Not in watchlist"}

    sentiment = get_stock_sentiment_summary(db, scrip_code)

    latest_price = (
        db.query(PriceSnapshot)
        .filter(PriceSnapshot.symbol == symbol)
        .order_by(PriceSnapshot.fetched_at.desc())
        .first()
    )

    if "message" in sentiment or latest_price is None:
        return {
            "scrip_code": scrip_code,
            "symbol": symbol,
            "message": "Insufficient sentiment or price data",
        }

    sentiment_positive = sentiment["net_sentiment"] > 0.1
    sentiment_negative = sentiment["net_sentiment"] < -0.1
    price_up = (latest_price.change_percent or 0) > 0
    price_down = (latest_price.change_percent or 0) < 0

    if sentiment_positive and price_up:
        composite_label = "Strong Positive"
    elif sentiment_negative and price_down:
        composite_label = "Strong Negative"
    elif sentiment_positive or sentiment_negative:
        composite_label = "Mixed"
    else:
        composite_label = "Neutral"

    return {
        "scrip_code": scrip_code,
        "symbol": symbol,
        "sentiment": sentiment,
        "latest_price": {
            "price": latest_price.price,
            "change_percent": latest_price.change_percent,
            "volume": latest_price.volume,
            "fetched_at": latest_price.fetched_at,
        },
        "composite_signal": composite_label,
    }

    