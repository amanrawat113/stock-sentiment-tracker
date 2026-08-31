import streamlit as st
import requests
from api.watchlist import WATCHLIST
from dotenv import load_dotenv
import os

load_dotenv()

API_BASE = os.environ["API_BASE"]

st.set_page_config(page_title="Stock Sentiment Tracker", layout="wide")
st.title("Stock Sentiment Tracker")
st.subheader("Market summary")
with st.spinner("Generating summary..."):
    summary_response = requests.get(
        f"{API_BASE}/market-summary",
        params={"min_announcements": 1, "threshold": 0.1},
    )
    summary_data = summary_response.json()

st.info(summary_data["summary"])

st.divider()

selected_symbol = st.selectbox("Select a stock", list(WATCHLIST.keys()))
scrip_code = WATCHLIST[selected_symbol]

response = requests.get(f"{API_BASE}/stocks/{scrip_code}/composite")
data = response.json()

if "message" in data:
    st.warning(data["message"])
else:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Net sentiment", data["sentiment"]["net_sentiment"])
    col2.metric("Announcements", data["sentiment"]["total_announcements"])
    col3.metric("Price", data["latest_price"]["price"])
    col4.metric("Composite", data["composite_signal"])

st.divider()

# Recent announcements for selected stock
st.subheader("Recent announcements")
ann_response = requests.get(f"{API_BASE}/stocks/{scrip_code}/announcements")
announcements = ann_response.json()

if not announcements:
    st.info("No announcements found for this stock.")
else:
    for a in announcements:
        col_a, col_b = st.columns([4, 1])
        col_a.write(a["headline"])
        label = a.get("sentiment_label", "unscored")
        if label == "positive":
            col_b.success(label)
        elif label == "negative":
            col_b.error(label)
        else:
            col_b.info(label)

st.divider()

# Market-wide alerts
st.subheader("Market alerts")
alerts_response = requests.get(f"{API_BASE}/alerts", params={"min_announcements": 1, "threshold": 0.1})
alerts = alerts_response.json()

if not alerts:
    st.info("No strong signals detected right now.")
else:
    for alert in alerts:
        col_a, col_b = st.columns([4, 1])
        col_a.write(f"{alert['company_name']} ({alert['symbol']})")
        col_b.metric("Net sentiment", alert["net_sentiment"], label_visibility="collapsed")