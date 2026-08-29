# Stock Sentiment Tracker

An AI-powered backend system that tracks Indian stock market sentiment by combining
live corporate announcements (BSE), live price data, FinBERT sentiment scoring, and
an LLM-generated natural-language market summary — with a Streamlit dashboard on top.

**Live demo:** https://stock-sentiment-tracker.streamlit.app/
**API base:** http://*.*.*.*:0000/stock-sentiment-tracker/api/v1

## Architecture

```
BSE Announcements API ─┐
                        ├─→ FastAPI ingestion → PostgreSQL (Supabase) → FinBERT sentiment
yfinance (live prices) ─┘                                                      │
                                                                                 ▼
                                                              Composite signal (sentiment + price)
                                                                                 │
                                                                                 ▼
                                                        Ollama Cloud LLM → natural-language summary
                                                                                 │
                                                                                 ▼
                                                              REST API → Streamlit dashboard
```

A background scheduler (APScheduler) runs ingestion, sentiment scoring, and price
updates automatically on an interval, no manual triggering needed once deployed.

## Tech stack

Python, FastAPI, SQLAlchemy, PostgreSQL (Supabase), FinBERT (HuggingFace transformers),
Ollama Cloud (LLM summaries), yfinance, Streamlit, Docker, AWS EC2, APScheduler

## Features

- Real-time BSE corporate announcement ingestion, filtered to a Nifty 50 watchlist
- Live price tracking via yfinance
- FinBERT-based sentiment scoring on announcement text
- Composite signal combining sentiment direction with price movement
- Market-wide alerts surfacing the strongest sentiment signals across the watchlist
- LLM-generated daily market summary (Ollama Cloud, gpt-oss:20b)
- Interactive Streamlit dashboard: stock selector, live metrics, announcement feed, alerts panel, AI summary banner
- Automated background scheduling for ingestion, scoring, and price updates

## Project structure

```
stock-sentiment-tracker/
├── main.py                 # FastAPI app entrypoint, scheduler setup
├── dashboard.py             # Streamlit dashboard
├── Dockerfile
├── requirements.txt
├── schedulers.py             # Background job definitions
├── api/
│   ├── v1.py                 # API routes
│   ├── service.py            # Business logic (BSE fetch, sentiment, LLM summary)
│   ├── models.py              # SQLAlchemy models (Announcement, PriceSnapshot)
│   └── watchlist.py            # Nifty 50 symbol/scrip code mapping
└── utils/
    └── database.py             # DB engine/session setup
```

## Setup

```bash
git clone https://github.com/amanrawat113/stock-sentiment-tracker.git
cd stock-sentiment-tracker
pip install -r requirements.txt
```

Create a `.env` file in the project root:
```
DATABASE_URL=postgresql://...
OLLAMA_API_KEY=your_key
```

Run the API:
```bash
uvicorn main:app --reload
```

Run the dashboard (separate terminal):
```bash
streamlit run dashboard.py
```

## Deployment

- **Backend:** Dockerized, deployed on AWS EC2 (t3.small, Ubuntu 26.04), with a
  security group scoped to SSH (restricted to owner IP), HTTP, and the app's custom port.
  Runs with `--restart unless-stopped` so it recovers automatically from crashes or
  instance reboots.
- **Dashboard:** Streamlit Community Cloud, connected directly to this GitHub repo —
  auto-redeploys on every push to `main`.
- **Database:** Supabase (hosted PostgreSQL).

## Engineering notes — things I actually debugged

- **BSE's announcements API is undocumented and unofficial.** Reverse-engineered the
  real endpoint and required headers via browser DevTools (bot-detection required
  specific `sec-ch-ua*` client hints, not just a User-Agent). Also discovered that
  `strCat=-1` (all categories) silently returns empty results on true multi-day date
  ranges, while single-day queries work fine and specific categories work on ranges —
  worked around this by looping day-by-day rather than requesting a range directly.
- **Ollama Cloud's `/api/chat` endpoint intermittently returned 401 despite a valid,
  dashboard-confirmed API key.** Isolated this to a per-model access issue —
  `gpt-oss:120b` failed consistently while `gpt-oss:20b` succeeded with the identical
  key and request shape — a known class of issue also reported by other developers on
  Ollama's GitHub.
- **FinBERT (via `torch`/`transformers`) crashed the app under Railway's free-tier
  memory limit** (~1GB), confirmed via an explicit `Killed` (OOM) log line. Rather than
  drop the finance-tuned sentiment model for a lighter alternative, moved deployment to
  AWS EC2 with adequate RAM, and switched to the CPU-only PyTorch build
  (`--extra-index-url https://download.pytorch.org/whl/cpu`) to avoid installing
  unnecessary CUDA/GPU dependencies that were also causing disk-space failures during
  Docker image builds.

## API endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/ingest` | POST | Fetch and store BSE announcements for a date range |
| `/prices/{symbol}` | POST | Fetch and store live price for one symbol |
| `/prices/ingest-all` | POST | Fetch and store live prices for the full watchlist |
| `/sentiment/score` | POST | Score pending announcements with FinBERT |
| `/stocks/{scrip_code}/sentiment` | GET | Aggregated sentiment summary for a stock |
| `/stocks/{scrip_code}/announcements` | GET | Raw announcement history for a stock |
| `/stocks/{scrip_code}/composite` | GET | Sentiment + price combined signal |
| `/alerts` | GET | Strongest sentiment signals across the watchlist |
| `/market-summary` | GET | LLM-generated natural-language market brief |

## Roadmap

- OAuth + user-specific saved watchlists
- Historical price/sentiment charting
- Expand beyond BSE to NSE announcements
- Confidence-weighted sentiment scoring (current LLM-based fallback returns a fixed confidence)
