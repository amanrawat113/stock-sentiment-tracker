from datetime import datetime, timedelta
from utils.database import SessionLocal
from api.service import (
    fetch_announcements_range,
    save_announcements,
    score_pending_announcements,
    ingest_all_prices,
)


def scheduled_ingest_announcements():
    db = SessionLocal()
    try:
        today = datetime.utcnow().strftime("%Y%m%d")
        yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y%m%d")
        raw = fetch_announcements_range(yesterday, today)
        inserted = save_announcements(db, raw)
        print(f"[Scheduler] Ingested {inserted} new announcements")
    finally:
        db.close()


def scheduled_score_sentiment():
    db = SessionLocal()
    try:
        scored = score_pending_announcements(db)
        print(f"[Scheduler] Scored {scored} announcements")
    finally:
        db.close()


def scheduled_ingest_prices():
    db = SessionLocal()
    try:
        saved = ingest_all_prices(db)
        print(f"[Scheduler] Saved {saved} price snapshots")
    finally:
        db.close()