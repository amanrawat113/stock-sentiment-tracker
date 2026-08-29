from fastapi import FastAPI
from api.v1 import router
from utils.database import engine
from sqlalchemy import text
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
