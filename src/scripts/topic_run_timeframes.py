import subprocess
import logging
import sys
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Cấu hình số lượng chủ đề đề xuất cho từng khung giờ:
    # 1h: 3 cụm, 6h: 5 cụm, 12h: 8 cụm, 24h: 10 cụm, 1 tuần (168h): 20 cụm
    timeframes_config = {
        1: 3,
        6: 5,
        12: 8,
        24: 10,
        168: 20
    }
    python_executable = sys.executable
    
    script_path = os.path.join(os.path.dirname(__file__), 'topic_detect.py')
    
    for tf, top_n in timeframes_config.items():
        logger.info(f"========== Bắt đầu chạy phát hiện chủ đề cho khoảng thời gian: {tf} giờ (top_n={top_n}) ==========")
        try:
            # Dùng subprocess để chạy script topic_detect.py
            subprocess.run(
                [python_executable, script_path, '--hours', str(tf), '--top_n', str(top_n)],
                check=True
            )
            logger.info(f"✅ Đã chạy thành công cho {tf} giờ.\n")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Lỗi khi chạy cho {tf} giờ: {e}\n")
            
if __name__ == '__main__':
    main()
