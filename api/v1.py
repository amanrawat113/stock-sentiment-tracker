from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from utils.database import get_db
from .service import *
from .llm import *

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/announcements")
def get_announcements(from_date: str, to_date: str):
    return fetch_announcements_range(from_date, to_date)


@router.post("/ingest")
def ingest(from_date: str, to_date: str, db: Session = Depends(get_db)):
    raw = fetch_announcements_range(from_date, to_date)
    inserted = save_announcements(db, raw)
    return {"fetched": len(raw), "inserted": inserted}


@router.post("/prices/ingest-all")
def ingest_all_prices_endpoint(db: Session = Depends(get_db)):
    saved = ingest_all_prices(db)
    return {"saved": saved, "total_watchlist": len(WATCHLIST)}


@router.post("/prices/{symbol}")
def ingest_price(symbol: str, db: Session = Depends(get_db)):
    price_data = fetch_price(symbol)
    record = save_price_snapshot(db, price_data)
    return {"saved": price_data}

@router.post("/sentiment/score")
def score_sentiment_endpoint(db: Session = Depends(get_db)):
    scored = score_pending_announcements(db)
    return {"scored": scored}


@router.get("/stocks/{scrip_code}/sentiment")
def get_stock_sentiment(scrip_code: int, db: Session = Depends(get_db)):
    return get_stock_sentiment_summary(db, scrip_code)


@router.get("/stocks/{scrip_code}/announcements")
def get_announcements_for_stock(scrip_code: int, limit: int = 20, db: Session = Depends(get_db)):
    return get_stock_announcements(db, scrip_code, limit)

@router.get("/alerts")
def get_alerts(min_announcements: int = 2, threshold: float = 0.3, db: Session = Depends(get_db)):
    return get_market_alerts(db, min_announcements, threshold)


@router.get("/stocks/{scrip_code}/composite")
def get_stock_composite(scrip_code: int, db: Session = Depends(get_db)):
    return get_composite_signal(db, scrip_code)

@router.get("/market-summary")
def market_summary(min_announcements: int = 1,threshold: float = 0.1,
    db: Session = Depends(get_db),
):
    alerts = get_market_alerts(db, min_announcements, threshold)
    summary = generate_market_summary(alerts)
    return {
        "summary": summary,
        "based_on_alerts": len(alerts),
        "alerts": alerts,
    }