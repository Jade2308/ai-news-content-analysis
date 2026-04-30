import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# Test import
try:
    from dashboard import render_article_detail, get_article_by_id
    print("✅ Dashboard imports OK")
except Exception as e:
    print(f"❌ Error: {e}")

