# AI-Powered Vietnamese News Analysis & Clickbait Detection

Real-time web mining, topic modeling, and automated clickbait detection for Vietnamese news articles.

> **Reference:** https://www.sciencedirect.com/science/article/pii/S2352340925008856

## Overview

This project implements an end-to-end pipeline for:
- **Automated Data Collection**: Continuous crawling of Vietnamese news from VNExpress and Tuổi Trẻ
- **Text Normalization**: HTML cleanup, deduplication, and text standardization
- **Clickbait Detection**: PhoBERT-based classification to identify misleading headlines
- **Hot Topic Modeling**: BERTopic clustering to surface trending topics across timeframes
- **Interactive Dashboard**: Real-time Streamlit UI to explore articles and analytics

The system runs on SQLite with automatic data pipelines orchestrated via APScheduler. A dark-themed Streamlit dashboard provides intuitive navigation through news articles, predictions, and insights.

---

## Prerequisites

- **Python**: ≥ 3.10
- **Git**: Required for cloning the repository
- **RAM**: ≥ 4GB recommended (PhoBERT model loading and inference)
- **Internet**: For initial data crawling and external dependencies

---

## Quick Start (5 Minutes)

### 1. Clone the Repository
```bash
git clone <https://github.com/Jade2308/ai-news-content-analysis>
cd ai-news-content-analysis
```

### 2. Create and Activate Virtual Environment

**Windows:**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Initialize the Database
```bash
python scripts/init_db.py
```
Creates `news.db` with standard schema. ⚠️ **Do not commit this file to the repository** — each developer seeds their local copy.

### 5. Train the Clickbait Model (One-time Setup)
```bash
python src/models/train_clickbait.py
```
Downloads and fine-tunes PhoBERT on the ViClickbait dataset (~5–15 minutes depending on hardware).  
The trained model is stored in `models/phobert_clickbait/` and loaded automatically in subsequent runs.

### 6. Populate Initial Data
```bash
python scripts/crawl_all.py
```
Crawls articles from all sources, deduplicates, and applies the trained classifier. Creates a baseline of data for the dashboard.

### 7. Launch the Dashboard
```bash
python main.py run
# or directly:
streamlit run dashboard.py
```
Open http://localhost:8501 in your browser.

---

## System Architecture

### Data Pipeline
```
Web Crawlers (VNExpress, Tuổi Trẻ)
    ↓
Text Normalization & Deduplication
    ↓
SQLite Database (articles table)
    ↓
PhoBERT Classification → Clickbait Predictions
    ↓
BERTopic Clustering → Hot Topics Detection
    ↓
Streamlit Dashboard (UI)
```

### Core Components

| Module | Purpose |
|--------|---------|
| `crawlers/` | Web scrapers for news sources (BeautifulSoup + Selenium) |
| `database/` | SQLite schema, migrations, and query helpers |
| `processing/` | Text cleaning, topic modeling, deduplication |
| `models/` | PhoBERT clickbait classifier and evaluation utilities |
| `scripts/` | Orchestration tasks (crawl, label, detect topics, scheduler) |
| `dashboard.py` | Streamlit application (dark theme) |
| `main.py` | CLI launcher for common tasks |

---

## Running Individual Tasks

### Label Unlabeled Articles (Inference)
Apply the trained PhoBERT model to any articles missing predictions:
```bash
python scripts/label_articles_with_predictions.py
```

### Detect Hot Topics
Run topic clustering for a single timeframe (e.g., 24 hours):
```bash
python scripts/detect_hot_topics.py
```

### Batch Topic Detection Across All Timeframes
Compute hot topics for 1h, 6h, 12h, 24h, and 7d windows:
```bash
python scripts/run_all_timeframes.py
```

### Discover New Categories
Crawl and extract potential news categories from article metadata:
```bash
python scripts/discover_categories.py
```

### Automated Background Scheduler
Run continuous crawling, classification, and topic detection (every 60 minutes):
```bash
python scripts/run_scheduler.py
```
This command launches a background process that:
1. Crawls new articles
2. Removes duplicates
3. Applies PhoBERT classifier
4. Runs topic clustering
5. Waits 60 minutes and repeats

---

## Dashboard Features

The Streamlit dashboard (`dashboard.py`) provides:
- **Dark Theme UI** with modern card layouts
- **Article Feed**: Browse recent articles with real-time predictions
- **Hot Topics View**: See trending topics across different timeframes (1h, 6h, 24h, 1 week)
- **Clickbait Stats**: Overview of classification results (counts, confidence scores)
- **Search Page**: Full-text search across title and summary
- **Article Detail Page**: Read full content with source and prediction badges

Access the dashboard after running step 7 above.

---

## Command-Line Interface (CLI)

The `main.py` script provides a convenient CLI:

```bash
# Run the dashboard on localhost:8501
python main.py run

# Initialize the database
python main.py initdb

# Interactive menu
python main.py menu

# Specify a custom port
python main.py run --port 9999
```

---

## Configuration & Environment

The project uses `config.py` for centralized settings:
- `DB_PATH`: Location of SQLite database (default: `news.db`)
- Model paths, crawler timeouts, and database paths are configured here

For sensitive data (API keys, credentials), create a `.env` file:
```env
# .env (not committed to repo)
OPENAI_API_KEY=sk-...
```
Load with `python-dotenv`:
```python
from dotenv import load_dotenv
load_dotenv()
```

---

## Model Information

### PhoBERT Clickbait Classifier
- **Type**: Transformer-based classification
- **Training Data**: ViClickbait dataset (~3,414 samples, 31.2% positive)
- **Labels**: `clickbait` (misleading headline) vs. `non-clickbait`
- **Location**: `models/phobert_clickbait/`
- **Training Time**: ~5–15 minutes on CPU; faster on GPU
- ⚠️ **Large File**: The model directory is excluded from Git (`.gitignore`). You must train it locally on first setup.

### BERTopic Topic Modeling
- Clusters similar articles into emergent topics
- Runs on configurable timeframes (1h, 6h, 12h, 24h, 7d)
- Results stored in `hot_topics` and `topic_articles` tables

---

## Repository Structure

```
ai-news-content-analysis/
├── crawlers/              # Web scraping modules
├── database/              # Schema, migrations, query helpers
├── models/                # AI models (clickbait classifier)
├── processing/            # Text cleaning, topic modeling
├── scripts/               # Automation tasks (crawl, label, detect_hot_topics, scheduler)
├── src/                   # Alternative source layout (models, crawlers, etc.)
├── dashboard.py           # Streamlit UI (dark theme)
├── main.py                # CLI launcher
├── config.py              # Global configuration
├── requirements.txt       # Python dependencies
├── news.db                # SQLite database (local only, not committed)
└── README.md              # This file
```

---

## .gitignore & Sensitive Files

The `.gitignore` file excludes:
- `news.db` and all `.db` files (local database instances)
- `models/phobert_clickbait/` and related trained models (too large)
- `.venv/`, `__pycache__/`, and Python artifacts
- `.streamlit/` config (Streamlit user configuration)
- `.env` (environment variables and secrets)
- Log files and IDE settings (`.vscode/`, `.idea/`)

---

## Troubleshooting

### **"Cannot import streamlit"**
Ensure `requirements.txt` has been installed:
```bash
pip install -r requirements.txt
```

### **"Model not found in models/phobert_clickbait/"**
Train the model on first setup:
```bash
python src/models/train_clickbait.py
```

### **Database locked error**
Close any other processes accessing `news.db` and retry.

### **Streamlit stays at loading**
- Check firewall/antivirus settings (may block localhost connections)
- Try running with explicit local binding:
  ```bash
  streamlit run dashboard.py --server.address 127.0.0.1 --server.port 8501
  ```

---

## Contributing

When adding new features:
1. Create a feature branch
2. Update `.gitignore` if new artifacts (large files, secrets) are introduced
3. Do not commit `.db` files or model checkpoints
4. Test locally with `streamlit run dashboard.py`
5. Update this README if adding new CLI commands or workflows

---

## License & Attribution

This project is part of a research initiative on Vietnamese news analysis. See individual modules for dependencies and their licenses.

---

## Cấu trúc dự án

```
news-mining/
├── config.py                  # DB_PATH và cấu hình chung
├── requirements.txt
├── scripts/
│   ├── init_db.py             # Tạo DB & schema
│   └── seed_db.py             # Crawl → clean → insert
├── crawlers/
│   ├── base_crawler.py        # Abstract base
│   ├── vnexpress_crawler.py   # Crawler VNExpress
│   ├── tuoitre_crawler.py     # Crawler Tuổi Trẻ
│   └── utils.py               # normalize_text, parse_time
├── core/
│   └── types.py               # Article dataclass (unified schema)
├── processing/
│   └── clean_text.py          # Làm sạch nội dung HTML/text
└── database/
    ├── schema.py              # init_db() – CREATE TABLE
    └── db.py                  # insert_article, get_all_articles, …
```

---

## Schema bài báo (chuẩn hóa)

| Trường             | Kiểu   | Mô tả                                 |
|--------------------|--------|---------------------------------------|
| `article_id`       | TEXT   | sha1(url)                             |
| `url`              | TEXT   | URL bài gốc (UNIQUE)                  |
| `source`           | TEXT   | `vnexpress` / `tuoitre`               |
| `category`         | TEXT   | Chuyên mục                            |
| `title`            | TEXT   | Tiêu đề (bắt buộc)                    |
| `summary`          | TEXT   | Tóm tắt / sapo                        |
| `content_text`     | TEXT   | Nội dung đã làm sạch                  |
| `author`           | TEXT   | Tác giả                               |
| `tags`             | TEXT   | Tags (phân cách bằng dấu phẩy)        |
| `published_at`     | TEXT   | "YYYY-MM-DD HH:MM:SS" hoặc NULL       |
| `crawled_at`       | TEXT   | "YYYY-MM-DD HH:MM:SS"                 |
| `content_html_raw` | TEXT   | HTML gốc (debug)                      |
| `fingerprint`      | TEXT   | sha1(content_text chuẩn hóa)           |

---

## Lưu ý về Rate Limit & Điều khoản sử dụng

- VNExpress: delay **1 giây** giữa mỗi bài.
- Tuổi Trẻ: delay **0.5 giây** giữa mỗi bài.
- Không crawl quá nhanh, tuân thủ điều khoản sử dụng của các trang báo.
- Chỉ sử dụng cho mục đích nghiên cứu/học thuật.

---

## Không commit DB

`news.db` đã được thêm vào `.gitignore`.  
Mỗi thành viên tự chạy `init_db.py` và `seed_db.py` để tạo bản cục bộ.

---

## Slide Outline

### Slide 0: Tiêu đề (Mở đầu)

**Tên đề tài:** Khai phá dữ liệu báo điện tử tiếng Việt theo thời gian gần thực phục vụ phân tích chủ đề và phát hiện clickbait  
**Môn:** Chuyên đề 2 – Khai phá dữ liệu Web  
**GVHD:** [Điền tên Giảng viên]  
**Nhóm:** 4 thành viên [Điền tên các thành viên]  
**Từ khóa:** Near real-time (1h), Clickbait detection, Topic mining, Trending dashboard

---

### Slide 1: Bài toán & Output *(Tiêu chí: Bài toán – 35đ)*

**Thực trạng:**  
- Tin “giật tít” (clickbait) gây nhiễu, giảm trải nghiệm và chất lượng tiếp nhận thông tin.  
- Người đọc cần: lọc clickbait + nắm bắt chủ đề nóng theo thời gian.

**Mục tiêu hệ thống (2 nhiệm vụ song song):**  
1. Phát hiện & lọc clickbait từ tiêu đề/đoạn dẫn.  
2. Gom cụm và theo dõi chủ đề nóng (trending topics) từ các bài báo chất lượng.

**Định nghĩa “gần thực” (Near real-time):**  
- Cập nhật mỗi 60 phút (crawl interval = 1h).  
- Mục tiêu latency: bài đăng mới → lên dashboard trong ≤ ~1 giờ.

**Output cụ thể:**  
- **Clickbait:** label (clickbait/non-clickbait) + score (0–1) + ngưỡng lọc bài.  
- **Trending topics:** danh sách topic theo thời gian + top keywords + bài đại diện + biểu đồ xu hướng.

---

### Slide 2: Hướng làm & Pipeline tổng thể *(Tiêu chí: Pipeline/Model – 35đ)*

**Luồng xử lý (end-to-end):**  
1. **Collect URLs:** Trang mục / RSS (nếu có)  
2. **Fetch & Parse:** Requests + BeautifulSoup  
3. **Tiền xử lý:** Bỏ HTML/boilerplate, chuẩn hóa unicode, chuẩn hóa text  
4. **Chuẩn hóa thời gian:** publish_datetime theo chuẩn ISO 8601  
5. **Lưu trữ:** Database + logging  
6. **Dedup (Loại bỏ trùng lặp):**  
    - Theo url/title  
    - Kết hợp SimHash/MinHash cho title + lead_paragraph  
7. **Hai nhánh mô hình:**  
    - *Clickbait Detection:* PhoBERT fine-tune → label + score  
    - *Topic Modeling/Trending:* BERTopic hoặc LDA → topic/keywords/trend  
8. **Dashboard:**  
    - Trending topics theo thời gian  
    - Thống kê clickbait theo nguồn/chuyên mục

**Vận hành near real-time:**  
- Scheduler/cron chạy mỗi 60 phút  
- Crawl bền vững: retry/backoff, timeout, rate limit, user-agent  
- Thiết kế mở: có thể giảm chu kỳ (ví dụ 15 phút) chỉ bằng việc đổi cấu hình

> **Lưu ý:** Khi thuyết trình, cần chèn hình ảnh minh họa pipeline kiến trúc hệ thống vào slide này.

---

### Slide 3: Dữ liệu, nguồn & tính khả thi *(Tiêu chí: Data & Feasibility – 25đ)*

**Nguồn thu thập:**  
- 4 báo điện tử lớn: VnExpress, Tuổi Trẻ, Thanh Niên, Dân Trí  
- Cập nhật định kỳ mỗi 60 phút (near real-time)

**Schema dữ liệu (bám sát ViClickbait-2025):**  
- `id` (unique identifier)  
- `url` (link bài)  
- `title` (headline)  
- `lead_paragraph` (đoạn dẫn/tóm tắt nếu có)  
- `category` (chuyên mục)  
- `publish_datetime` (ISO 8601)  
- `source` (tên báo)  
- `thumbnail_url` (nếu có)  
- *(Tuỳ chọn)* `content` (hỗ trợ topic modeling tốt hơn)

**Tiền xử lý & Dedup:**  
- Loại bỏ HTML/boilerplate, chuẩn hóa unicode, loại ký tự rác  
- Dedup theo url/title + SimHash/MinHash trên title + lead_paragraph

**Tính khả thi:**  
- Sử dụng dữ liệu thật, cập nhật liên tục theo chu kỳ 1h  
- Công cụ Python phổ biến, dễ triển khai, hoàn toàn demo được trong thời gian môn học  
- Mở rộng nguồn báo dễ dàng theo dạng “module crawler theo từng site”

---

### Slide 4: Baseline từ bài báo khoa học *(Tiêu chí: Baseline paper – 25đ)*

**Paper baseline:**  
- “ViClickbait-2025: A comprehensive dataset for Vietnamese clickbait detection” (Data in Brief, 2025)

**Thông tin quan trọng từ Paper:**  
- Dataset gồm 3,414 tiêu đề  
- Tỷ lệ clickbait chiếm 31.2%  
- Độ tin cậy gán nhãn cao: Cohen’s Kappa = 0.822  
- Đặc trưng clickbait: tạo “khoảng trống tò mò”, dùng từ cảm xúc mạnh, cường điệu hoá...

**Ý nghĩa baseline:**  
- Có dataset chuẩn + định nghĩa rõ ràng → đảm bảo tính “research-level”  
- Là cơ sở vững chắc để huấn luyện và so sánh mô hình clickbait cho hệ thống

---

### Slide 5: Áp dụng baseline & Cách đánh giá *(Tiêu chí: Baseline + đo lường)*

**A. Nhánh Clickbait Detection (PhoBERT fine-tune):**  
- Training data: ViClickbait-2025  
- Inference: Chạy trên dữ liệu crawl mỗi 1h → xuất label + score  
- Metrics đánh giá: Precision, Recall, F1-score, confusion matrix  
- Mục tiêu: Mô hình đủ tốt để lọc bài clickbait trước khi đưa vào phân tích chủ đề

**B. Nhánh Topic Modeling & Trending (BERTopic/LDA):**  
- Input: Ưu tiên bài non-clickbait (đã được lọc từ nhánh A)  
- Trending: Rolling window 24 giờ, cập nhật mỗi 60 phút  
- Đánh giá:  
  - Đo lường Topic coherence (Cv/UMass)  
  - Đánh giá thủ công nhỏ (nhóm tự review một số topic) do không có ground-truth topic

---

### Slide 6: Kế hoạch thực hiện & phân công *(Tiêu chí: Kế hoạch – 15đ)*

**Timeline 6 tuần:**  
- **Tuần 1:** Chốt schema + Database + scheduler/logging  
- **Tuần 2:** Crawl & lưu dữ liệu 4 báo (xử lý retry/rate-limit, đảm bảo ổn định)  
- **Tuần 3:** Preprocess + dedup (url/title + SimHash/MinHash)  
- **Tuần 4:** Train/eval mô hình PhoBERT clickbait (Precision/Recall/F1) + tích hợp inference  
- **Tuần 5:** Triển khai Topic modeling + trending (24h window) + đo lường coherence/review  
- **Tuần 6:** Xây dựng Dashboard + test end-to-end + chuẩn bị demo & báo cáo

**Phân công 4 thành viên:**  
- Thành viên 1: Xây dựng Crawler + scheduler/cron + logging  
- Thành viên 2: Preprocessing + thiết kế schema DB + thuật toán dedup  
- Thành viên 3: Phụ trách Clickbait model (PhoBERT) + evaluation (F1/PR/RC)  
- Thành viên 4: Phụ trách Topic/trending + làm dashboard + tích hợp hệ thống để demo

**Tóm tắt 3 giá trị cốt lõi của đề tài:**  
1. **Research-level:** Có baseline paper rõ ràng + mô hình chuẩn + metrics đánh giá minh bạch  
2. **Khả thi:** Vận hành near real-time 1h, scope dự án vừa sức để hoàn thiện trong 6 tuần  
3. **Data thật & Đo lường được:** Đánh giá F1 cho clickbait + coherence cho topic + có sản phẩm demo dashboard thực tế

---
