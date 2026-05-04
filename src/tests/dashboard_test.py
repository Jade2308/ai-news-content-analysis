import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Test import and sanitization
try:
    from src.streamlit.dashboard import prepare_article_records
    import pandas as pd

    print("✅ Imported prepare_article_records")

    df = pd.DataFrame({
        "article_id": [1, 2, 3, 4],
        "title": ["A", "B", "C", "D"],
        "prediction_score": [None, "0.5", 1.2, "nan"],
    })

    records = prepare_article_records(df)
    scores = [r.get("prediction_score") for r in records]
    expected = [0.0, 0.5, 1.0, 0.0]
    assert all(abs(a - b) < 1e-6 for a, b in zip(scores, expected)), f"Scores {scores} != expected {expected}"
    print("✅ prepare_article_records sanitizes prediction_score as expected")

except Exception as e:
    print(f"❌ Test failed: {e}")

