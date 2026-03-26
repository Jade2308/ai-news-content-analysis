import logging
from crawlers._tuoitre import TuoitreCrawler

logger = logging.getLogger('check_tuoitre')

def run_check():
    """Run a quick diagnostic for TuoiTre crawler."""
    print("Checking TuoiTre crawler...")
    try:
        crawler = TuoitreCrawler(category='thoi-su')
        articles = crawler.run(limit=5)
        if articles:
            print(f"✅ Success! Found {len(articles)} articles.")
            print(f"Sample Title: {articles[0].title}")
        else:
            print("❌ Failure: No articles found.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_check()
