import time
import subprocess
import sys
import logging
import os
from datetime import datetime, timedelta

from src.database.db import clean_old_data

# Đảm bảo chạy đúng thư mục gốc dự án
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(project_root)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - ⏰ SCHEDULER - %(message)s'
)

def run_job():
    logging.info("ĐANG KÍCH HOẠT SCRIPT `crawl_hourly.py`...")
    try:
        # sys.executable đảm bảo dùng đúng file python trong môi trường ảo (.venv) hiện tại
        subprocess.run([sys.executable, "src/scripts/crawl_hourly.py"])

        logging.info("ĐANG KÍCH HOẠT SCRIPT `topic_detect.py` CHO CÁC MỐC HOT TOPICS...")
        topic_jobs = [
            (1, 3),
            (6, 5),
            (24, 10),
            (168, 20),
        ]
        for hours, top_n in topic_jobs:
            logging.info(f"-> Phân tích hot_topics {hours}h (top_n={top_n})")
            subprocess.run([
                sys.executable,
                "src/scripts/topic_detect.py",
                "--hours",
                str(hours),
                "--top_n",
                str(top_n),
            ])

        # Dọn dẹp dữ liệu cũ hàng ngày lúc 3 giờ sáng
        now = datetime.now()
        if now.hour == 3 and now.minute < 1:
            logging.info("🧹 Thực hiện dọn dẹp dữ liệu cũ (> 14 ngày)...")
            try:
                deleted_articles, deleted_topics, deleted_topic_articles = clean_old_data(days=14)
                logging.info(f"✅ Dọn dẹp xong: {deleted_articles} articles, {deleted_topics} topics, {deleted_topic_articles} liên kết")
            except Exception as e:
                logging.error(f"❌ Lỗi dọn dẹp dữ liệu: {e}")

        logging.info("✅ HOÀN TẤT PHIÊN LÀM VIỆC!")
    except Exception as e:
        logging.error(f"❌ Lỗi khi chạy: {e}")

if __name__ == "__main__":
    logging.info("=" * 60)
    logging.info("🚀 HỆ THỐNG CRAWL TỰ ĐỘNG ĐÚNG GIỜ ĐÃ KHỞI ĐỘNG")
    logging.info("Hệ thống sẽ chạy một lần đầu tiên, sau đó dóng mốc thời gian thực đúng vào phút 00 của mỗi giờ (VD: 17:00, 18:00...).")
    logging.info("Nhấn Ctrl + C để dừng hệ thống.")
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
        
        logging.info(f"⏳ Cữ tiếp theo sẽ chạy lúc đúng: {next_hour.strftime('%H:%M:%S')}")
        logging.info(f"Đang chờ {int(sleep_seconds // 60)} phút {int(sleep_seconds % 60)} giây nữa...")
        
        try:
            # Cho hệ thống ngủ đúng tới số giây cần thiết
            time.sleep(sleep_seconds)
            
            # Đánh thức lên và làm việc
            run_job()
            
        except KeyboardInterrupt:
            logging.info("\n🛑 Đã nhận lệnh dừng từ người dùng. Tắt hệ thống tự động.")
            break
