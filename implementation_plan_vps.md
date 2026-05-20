# BẢNG KẾ HOẠCH TRIỂN KHAI VÀ NÂNG CẤP DỰ ÁN AI NEWS LÊN CLOUD 24/7

Kế hoạch này giúp bạn thực hiện quá trình nâng cấp hệ thống một cách trơn tru, bảo vệ dữ liệu cũ và thiết lập môi trường chạy 24/7 tối ưu nhất trên VPS 1GB RAM của DigitalOcean.

---

## 📅 BẢNG KẾ HOẠCH TỪNG BƯỚC (ROADMAP)

| Giai đoạn | Bước | Công việc chi tiết | Công cụ thực hiện | Lệnh / Hành động chính | Trạng thái |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **GIAI ĐOẠN 1:<br>DỌN DẸP &<br>SAO LƯU HỆ THỐNG CŨ** | **1.1** | Tải database cũ về máy cá nhân làm bản backup bảo vệ dữ liệu | **WinSCP** | Tải file `news.db` từ thư mục `data/` trên VPS về máy local. | ⬜ Chưa làm |
| | **1.2** | Tìm và tắt tiến trình Streamlit cũ đang chạy chiếm cổng | **Terminal (SSH)** | `pkill -f streamlit`<br>hoặc `kill -9 $(lsof -t -i:8501)` | ⬜ Chưa làm |
| | **1.3** | Tìm và tắt tiến trình Crawler cũ đang chạy ngầm | **Terminal (SSH)** | `pkill -f python` | ⬜ Chưa làm |
| | **1.4** | Tắt các lệnh Cron Job tự động cũ để tránh xung đột | **Terminal (SSH)** | Gõ `crontab -e`, thêm dấu `#` vào các dòng lệnh crawl cũ. | ⬜ Chưa làm |
| **GIAI ĐOẠN 2:<br>CHUẨN BỊ MÃ NGUỒN<br>(LOCAL MACHINE)** | **2.1** | Tạo thư mục sạch `ai-news-production` để chuẩn bị upload | **File Explorer (Local)** | Tạo folder mới, copy `src/`, `main.py`, `.env` của dự án vào. | ⬜ Chưa làm |
| | **2.2** | Tích hợp dữ liệu cũ vào bộ cài mới | **File Explorer (Local)** | Tạo folder `data/` trong `ai-news-production` rồi paste file `news.db` đã backup ở Bước 1.1 vào. | ⬜ Chưa làm |
| | **2.3** | Chỉ định duy nhất model PhoBERT đã train | **File Explorer (Local)** | Copy duy nhất folder `models/phobert_clickbait/` vào thư mục mới. Xóa các model đối chứng khác. | ⬜ Chưa làm |
| | **2.4** | Sửa `requirements.txt` sang bản siêu nhẹ dùng CPU | **VS Code / Notepad** | Sửa thư viện `torch` thành: `--extra-index-url https://download.pytorch.org/whl/cpu` và `torch`. | ⬜ Chưa làm |
| **GIAI ĐOẠN 3:<br>CẤU HÌNH SWAP RAM<br>(VPS DIGITALOCEAN)** | **3.1** | Tạo và định dạng file Swap dung lượng 4GB | **Terminal (SSH)** | `sudo fallocate -l 4G /swapfile`<br>`sudo chmod 600 /swapfile`<br>`sudo mkswap /swapfile` | ⬜ Chưa làm |
| | **3.2** | Kích hoạt Swap và cấu hình tự chạy khi khởi động lại VPS | **Terminal (SSH)** | `sudo swapon /swapfile`<br>Thêm dòng tự khởi động vào file `/etc/fstab` | ⬜ Chưa làm |
| | **3.3** | Điều chỉnh độ nhạy Swappiness tối ưu cho RAM thật | **Terminal (SSH)** | `sudo sysctl vm.swappiness=10`<br>Lưu cấu hình vào `/etc/sysctl.conf` | ⬜ Chưa làm |
| **GIAI ĐOẠN 4:<br>UPLOAD CODE &<br>CÀI ĐẶT MÔI TRƯỜNG** | **4.1** | Upload thư mục `ai-news-production` lên VPS | **WinSCP** | Kéo thả thư mục từ máy local lên thư mục `/root` trên VPS. | ⬜ Chưa làm |
| | **4.2** | Cài đặt các gói hệ thống cho Ubuntu | **Terminal (SSH)** | `sudo apt update`<br>`sudo apt install python3-pip python3-venv sqlite3 libgomp1 -y` | ⬜ Chưa làm |
| | **4.3** | Tạo Môi trường ảo Python và cài đặt các thư viện lõi | **Terminal (SSH)** | `python3 -m venv venv`<br>`source venv/bin/activate`<br>`pip install -r requirements.txt` | ⬜ Chưa làm |
| **GIAI ĐOẠN 5:<br>CHẠY NGẦM 24/7 VỚI PM2** | **5.1** | Cài đặt phần mềm quản lý process PM2 | **Terminal (SSH)** | `sudo apt install npm -y`<br>`sudo npm install pm2 -g` | ⬜ Chưa làm |
| | **5.2** | Khởi chạy Scheduler tự động crawl mỗi giờ | **Terminal (SSH)** | `pm2 start venv/bin/python --name "ai-news-scheduler" -- src/scripts/sched_run.py` | ⬜ Chưa làm |
| | **5.3** | Khởi chạy giao diện Streamlit Dashboard | **Terminal (SSH)** | `pm2 start venv/bin/streamlit --name "ai-news-dashboard" -- run src/streamlit/dashboard_ui.py --server.port 8501` | ⬜ Chưa làm |
| | **5.4** | Lưu trạng thái dịch vụ PM2 để tự khôi phục khi VPS reboot | **Terminal (SSH)** | `pm2 save`<br>`pm2 startup` | ⬜ Chưa làm |
| **GIAI ĐOẠN 6:<br>MỞ CỔNG & KIỂM TRA** | **6.1** | Mở cổng tường lửa trên VPS | **Terminal (SSH)** | `sudo ufw allow 8501`<br>`sudo ufw reload` | ⬜ Chưa làm |
| | **6.2** | Truy cập giao diện thực tế và xem log hoạt động ngầm | **Trình duyệt & Terminal** | Truy cập `http://<IP_VPS>:8501`<br>Xem log với lệnh: `pm2 logs` | ⬜ Chưa làm |

---

## ⚠️ CÁC LƯU Ý QUAN TRỌNG KHI THỰC HIỆN

> [!WARNING]
> **Không bỏ qua bước tạo Swap (Giai đoạn 3):** Nếu bạn cài đặt `torch` và load mô hình PhoBERT mà không kích hoạt Swap RAM, máy chủ VPS của bạn sẽ bị đơ cứng, ngắt kết nối SSH và bị sập hoàn toàn.

> [!TIP]
> **Tận dụng tối đa dữ liệu cũ:** Bằng việc tải `news.db` ở bước 1.1 về máy local rồi tích hợp vào thư mục upload ở bước 2.2, toàn bộ dữ liệu bạn đã dày công thu thập trước đây sẽ được kế thừa hoàn hảo.

> [!IMPORTANT]
> **Bản cài PyTorch CPU:** Hãy đảm bảo file `requirements.txt` của bạn đã được thay đổi như hướng dẫn ở bước 2.4. Bản PyTorch CPU chạy suy luận cực kỳ tốt trên VPS và giảm tới 90% dung lượng tải xuống của máy chủ so với bản GPU mặc định.
