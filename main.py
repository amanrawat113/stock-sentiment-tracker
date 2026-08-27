from fastapi import FastAPI
from api.v1 import router

app = FastAPI(title="Stock Sentiment Tracker")

@app.get("/")
async def root():
    return {"message": "Welcome to the Stock Sentiment Tracker Service! Go to /docs for documentation."}

CONTEXT_PATH = "/stock-sentiment-tracker/api/v1"

app.include_router(router, prefix=CONTEXT_PATH)
