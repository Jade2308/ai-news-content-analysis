# HƯỚNG DẪN TRIỂN KHAI DỰ ÁN AI NEWS LÊN VPS DIGITALOCEAN (1GB RAM / CPU-ONLY)

Tài liệu này hướng dẫn bạn cấu hình máy chủ VPS Ubuntu 1GB RAM chạy ổn định dự án **AI News Content Analysis** 24/7 bằng cách sử dụng **Swap Space (RAM ảo)** để chạy mô hình AI nội bộ (PhoBERT & BERTopic) mà không lo bị tràn bộ nhớ (Out of Memory).

---

## 📋 TỔNG QUAN CHIẾN LƯỢC TRIỂN KHAI

1. **Cấu hình Swap Space (RAM ảo - 4GB)**: Chuyển 4GB từ ổ cứng SSD làm bộ nhớ RAM dự phòng. Đây là chìa khóa giúp VPS 1GB RAM khởi động được PyTorch, PhoBERT và BERTopic.
2. **Tối ưu hóa môi trường CPU-only**: Cài đặt PyTorch phiên bản CPU để tiết kiệm dung lượng ổ cứng (chỉ ~150MB thay vì ~2.5GB của bản CUDA/GPU) và giảm ngốn RAM.
3. **Lọc file & Upload bằng WinSCP**: Chỉ upload mã nguồn và thư mục chứa mô hình PhoBERT đã train (`models/phobert_clickbait`). Loại bỏ các mô hình so sánh và báo cáo khác để giữ ổ cứng sạch sẽ.
4. **Quản lý chạy ngầm 24/7 với PM2**: Giúp Crawler và Streamlit tự khởi chạy và tự phục hồi khi có sự cố.

---

## BƯỚC 1: TẠO SWAP RAM (RAM ẢO) TRÊN VPS UBUNTU

Thực hiện các lệnh sau trên **Terminal (SSH)** của VPS với quyền `root` hoặc `sudo` để tạo thêm 4GB RAM ảo từ ổ cứng:

```bash
# 1. Tạo file swap kích thước 4GB (4G)
sudo fallocate -l 4G /swapfile

# 2. Phân quyền bảo mật cho file swap (chỉ root được đọc/ghi)
sudo chmod 600 /swapfile

# 3. Định dạng file thành không gian Swap
sudo mkswap /swapfile

# 4. Kích hoạt Swap ngay lập tức
sudo swapon /swapfile

# 5. Kiểm tra xem Swap đã hoạt động chưa
sudo swapon --show
# (Bạn sẽ thấy dòng /swapfile file 4G ... hiển thị)

# 6. Thiết lập tự động kích hoạt Swap mỗi khi khởi động lại VPS
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 7. Điều chỉnh tham số để hệ thống ưu tiên dùng RAM thật trước khi chạm vào Swap
# Giá trị 10 nghĩa là chỉ dùng Swap khi RAM thật còn dưới 10%
sudo sysctl vm.swappiness=10
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
```

---

## BƯỚC 2: CHUẨN BỊ MÃ NGUỒN TRÊN MÁY LOCAL & UPLOAD BẰNG WINSCP

### 2.1 Cắt tỉa thư mục trước khi upload
Bạn tạo một thư mục mới trên máy tính của bạn tên là `ai-news-production`, sau đó copy cấu trúc thư mục sau từ dự án gốc vào đó:

```text
ai-news-production/
├── src/                      # Copy toàn bộ thư mục src
├── main.py                   # File chạy chính
├── requirements.txt          # File thư viện (Sẽ sửa ở bước dưới)
├── .env                      # Chứa các biến môi trường (Ví dụ: GEMINI_API_KEY)
└── models/
    └── phobert_clickbait/    # CHỈ COPY duy nhất thư mục model PhoBERT này
```

> [!IMPORTANT]
> **Không copy** các thư mục sau để tránh tốn dung lượng upload:
> - Thư mục `.git/` (nặng và không dùng trên production).
> - Thư mục `.venv/` hoặc `__pycache__/` cũ của máy local.
> - Thư mục `models/visobert_clickbait/` và `models/xlm_roberta_clickbait/` (các mô hình so sánh lúc báo cáo).
> - Thư mục `data/` chứa file `news.db` cũ của máy local (VPS sẽ tự khởi tạo database mới tinh, hoặc nếu bạn muốn giữ data cũ thì chỉ upload duy nhất file `news.db` sang thư mục `data/` trên VPS).
> - Các file báo cáo như `ĐACS 4.docx`, `dacs4_content.txt`.

### 2.2 Sửa file `requirements.txt` dành cho CPU
Mở file `requirements.txt` trong thư mục `ai-news-production` bằng Notepad hoặc VS Code và thay thế nội dung bằng cấu hình CPU-only dưới đây để tránh cài đặt bản GPU nặng 2.5GB:

```txt
requests
beautifulsoup4
lxml
APScheduler
SQLAlchemy
pandas
plotly
streamlit
python-dotenv
# Chỉ định cài đặt PyTorch phiên bản CPU để tiết kiệm bộ nhớ
--extra-index-url https://download.pytorch.org/whl/cpu
torch
transformers
scikit-learn
numpy
tqdm
gensim
underthesea
bertopic
accelerate
google-generativeai
```

### 2.3 Upload dữ liệu bằng WinSCP
1. Mở **WinSCP** và kết nối vào VPS DigitalOcean của bạn.
2. Kéo thả toàn bộ thư mục `ai-news-production` từ máy cá nhân lên thư mục `/root` (hoặc `/home/ubuntu`) trên VPS.

---

## BƯỚC 3: CÀI ĐẶT MÔI TRƯỜNG & THƯ VIỆN TRÊN VPS (TERMINAL)

Khi WinSCP đã upload hoàn tất toàn bộ code và weights của model PhoBERT lên VPS, hãy mở **Terminal** để cấu hình Python:

```bash
# 1. Di chuyển vào thư mục dự án trên VPS
cd ~/ai-news-production

# 2. Cài đặt các gói hệ thống cần thiết cho Python và SQLite3
sudo apt update
sudo apt install python3-pip python3-venv sqlite3 libgomp1 -y

# 3. Tạo môi trường ảo riêng biệt (.venv) để tránh xung đột hệ thống
python3 -m venv venv

# 4. Kích hoạt môi trường ảo
source venv/bin/activate

# 5. Nâng cấp pip lên bản mới nhất
pip install --upgrade pip

# 6. Cài đặt các thư viện trong requirements.txt (Quá trình này có thể mất 5-10 phút vì build trên Swap RAM)
pip install -r requirements.txt
```

---

## BƯỚC 4: THIẾT LẬP CHẠY 24/7 VỚI PM2

Để đảm bảo Dashboard Streamlit và Scheduler Crawl chạy ngầm liên tục ngay cả khi bạn tắt máy tính cá nhân hoặc tắt cửa sổ Terminal, chúng ta sử dụng **PM2** (Process Manager):

### 4.1 Cài đặt Node.js và PM2 trên VPS
```bash
sudo apt install npm -y
sudo npm install pm2 -g
```

### 4.2 Cấu hình PM2 chạy các script dự án
Đảm bảo bạn vẫn đang đứng ở thư mục `~/ai-news-production` và đã kích hoạt môi trường ảo (`source venv/bin/activate`).

```bash
# 1. Chạy Scheduler (Crawl dữ liệu và phân loại tự động mỗi giờ)
pm2 start venv/bin/python --name "ai-news-scheduler" -- src/scripts/sched_run.py

# 2. Chạy Streamlit Dashboard (Hiển thị giao diện người dùng trên cổng 8501)
pm2 start venv/bin/streamlit --name "ai-news-dashboard" -- run src/streamlit/dashboard_ui.py --server.port 8501

# 3. Lưu cấu hình khởi động để tự chạy lại khi VPS bị khởi động lại (Reboot)
pm2 save
pm2 startup
```

### 4.3 Cách kiểm tra trạng thái hoạt động trên VPS
```bash
# Xem danh sách các tiến trình đang chạy ngầm
pm2 status

# Xem log hoạt động thời gian thực (giúp bạn theo dõi tiến độ crawl và phân loại)
pm2 logs ai-news-scheduler

# Xem log của Streamlit Dashboard
pm2 logs ai-news-dashboard
```

---

## BƯỚC 5: MỞ PORT TRÊN MÁY CHỦ ĐỂ TRUY CẬP STREAMLIT

Mặc định Ubuntu trên DigitalOcean có tường lửa bảo vệ. Bạn cần mở cổng `8501` để truy cập được Dashboard từ trình duyệt:

```bash
sudo ufw allow 8501
sudo ufw reload
```

Bây giờ bạn hãy mở trình duyệt trên máy tính cá nhân và truy cập:
`http://<IP_CỦA_VPS_DIGITALOCEAN>:8501`

---

## 🛠️ MỘT SỐ LƯU Ý KHI VẬN HÀNH SẢN PHẨM TRÊN VPS 1GB RAM

1. **Tốc độ suy luận (Inference Speed)**: Do chạy trên CPU và có sự hỗ trợ của RAM ảo (Swap), quá trình phân loại clickbait của PhoBERT cho mỗi bài viết mới sẽ mất khoảng **1 - 3 giây/bài**. Điều này hoàn toàn bình thường và không ảnh hưởng vì Scheduler chạy ngầm mỗi giờ một lần.
2. **Quy mô Scheduler**: Script `crawl_hourly.py` đã được thiết kế tối ưu (chỉ lấy tối đa 10 bài mới nhất mỗi chuyên mục và dừng ngay khi thấy bài cũ), giúp giảm tối đa tải cho CPU và RAM. Bạn không nên chạy full-crawl toàn bộ lịch sử web trên VPS này.
3. **Database**: SQLite3 (`data/news.db`) cực kỳ bền bỉ và tốn rất ít tài nguyên, hoàn hảo cho cấu hình VPS hiện tại.
