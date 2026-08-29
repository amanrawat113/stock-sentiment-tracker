from transformers import pipeline

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

label, score = score_sentiment("Reliance Industries reports record quarterly profit, beats analyst estimates")
print(label, score)