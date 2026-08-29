from fastapi import FastAPI
from api.v1 import router
from utils.database import engine

from sqlalchemy import text
from apscheduler.schedulers.background import BackgroundScheduler
from api.schedulers import (
    scheduled_ingest_announcements,
    scheduled_score_sentiment,
    scheduled_ingest_prices,
)

scheduler = BackgroundScheduler()
app = FastAPI(title="Stock Sentiment Tracker")

@app.get("/")
async def root():
    return {"message": "Welcome to the Stock Sentiment Tracker Service! Go to /docs for documentation."}

CONTEXT_PATH = "/stock-sentiment-tracker/api/v1"

app.include_router(router, prefix=CONTEXT_PATH)

@app.on_event("startup")
def verify_db_connection():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("Database connection verified successfully")


@app.on_event("startup")
def start_scheduler():
    scheduler.add_job(scheduled_ingest_announcements, "interval", hours=1, id="ingest_announcements")
    scheduler.add_job(scheduled_score_sentiment, "interval", minutes=30, id="score_sentiment")
    scheduler.add_job(scheduled_ingest_prices, "interval", minutes=30, id="ingest_prices")
    scheduler.start()
    print("Scheduler started")


@app.on_event("shutdown")
def stop_scheduler():
    scheduler.shutdown()