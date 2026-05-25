import logging
import os
import sys
import time
from datetime import datetime, timedelta

# Ensure project root (parent of `src`) is on sys.path.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

from src.workflows import run_crawl

logging.basicConfig(level=logging.INFO, format="%(asctime)s - SCHEDULER - %(message)s")


def run_job():
    logging.info("Starting hourly crawl job...")
    try:
        run_crawl(mode="hourly")
        logging.info("Hourly crawl job finished.")
    except Exception as exc:  # noqa: BLE001
        logging.error("Job failed: %s", exc)

if __name__ == "__main__":
    logging.info("=" * 60)
    logging.info("Hourly scheduler started.")
    logging.info("Runs once immediately, then at minute 00 each hour.")
    logging.info("Press Ctrl + C to stop.")
    logging.info("=" * 60)
    
    # Chạy lần đầu ngay lúc vừa bấm nút khởi động
    run_job()
    
    while True:
        now = datetime.now()
        
        # Tính toán mốc giờ đúng tiếp theo
        # Ví dụ hiện tại 16:47:15 -> Tính ra mốc: 17:00:00 cùng ngày
        next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        
        # Khoảng thời gian lẻ còn lại để ngủ
        sleep_seconds = (next_hour - now).total_seconds()
        
        logging.info("Next run at: %s", next_hour.strftime("%H:%M:%S"))
        logging.info(
            "Sleeping for %s minutes %s seconds...",
            int(sleep_seconds // 60),
            int(sleep_seconds % 60),
        )
        
        try:
            # Cho hệ thống ngủ đúng tới số giây cần thiết
            time.sleep(sleep_seconds)
            
            # Đánh thức lên và làm việc
            run_job()
            
        except KeyboardInterrupt:
            logging.info("\nStop signal received. Shutting down scheduler.")
            break
