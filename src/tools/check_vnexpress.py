import logging
from crawlers._vnexpress import VNExpressCrawler

logger = logging.getLogger('check_vnexpress')

def run_check():
    """Run a quick diagnostic for VNExpress crawler."""
    print("Checking VNExpress crawler...")
    try:
        crawler = VNExpressCrawler(category='thoi-su')
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
