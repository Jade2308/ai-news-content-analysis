# news-mining – Module 1: Thu thập & Chuẩn hóa Dữ liệu

> **Web Mining** – crawl, clean, và lưu bài báo tiếng Việt từ VNExpress & Tuổi Trẻ vào SQLite.

---

## Cài đặt

```bash
pip install -r requirements.txt
```

Yêu cầu Python ≥ 3.10.

---

## Khởi tạo DB

```bash
python scripts/init_db.py
```

Tạo file `news.db` với schema chuẩn (nếu chưa tồn tại).  
> **Lưu ý:** `news.db` **không** được commit vào repo. Mỗi thành viên tự seed DB cục bộ.

---

## Seed dữ liệu

```bash
# Crawl VNExpress chuyên mục kinh-doanh, tối đa 200 bài
python scripts/seed_db.py --source vnexpress --category kinh-doanh --limit 200

# Crawl Tuổi Trẻ chuyên mục thời sự, tối đa 200 bài
python scripts/seed_db.py --source tuoitre --category thoi-su --limit 200

# Crawl tất cả nguồn với limit mặc định (50 bài mỗi nguồn)
python scripts/seed_db.py --source all --limit 50
```

### Tham số `seed_db.py`

| Tham số | Mô tả | Mặc định |
|---|---|---|
| `--source` | `vnexpress` / `tuoitre` / `all` | `all` |
| `--category` | Chuyên mục (tuỳ nguồn) | `kinh-doanh` / `thoi-su` |
| `--limit` | Số bài tối đa mỗi nguồn | `50` |
| `--db-path` | Đường dẫn DB | `news.db` (từ `config.py`) |

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

## Schema bài báo (unified)

| Field | Kiểu | Mô tả |
|---|---|---|
| `article_id` | TEXT | sha1(url) |
| `url` | TEXT | URL bài gốc (UNIQUE) |
| `source` | TEXT | `vnexpress` / `tuoitre` |
| `category` | TEXT | Chuyên mục |
| `title` | TEXT | Tiêu đề (bắt buộc) |
| `summary` | TEXT | Tóm tắt / sapo |
| `content_text` | TEXT | Nội dung đã làm sạch |
| `author` | TEXT | Tác giả |
| `tags` | TEXT | Tags (phân cách bằng dấu phẩy) |
| `published_at` | TEXT | "YYYY-MM-DD HH:MM:SS" hoặc NULL |
| `crawled_at` | TEXT | "YYYY-MM-DD HH:MM:SS" |
| `content_html_raw` | TEXT | HTML gốc (debug) |
| `fingerprint` | TEXT | sha1(content_text chuẩn hoá) |

---

## Lưu ý Rate Limit & ToS

- VNExpress: delay **1 giây** giữa mỗi bài.
- Tuổi Trẻ: delay **0.5 giây** giữa mỗi bài.
- Vui lòng **không** crawl quá nhanh và tôn trọng điều khoản sử dụng của các trang báo.
- Chỉ dùng cho mục đích nghiên cứu / học thuật.

---

## Không commit DB

`news.db` đã được thêm vào `.gitignore`.  
Mỗi thành viên tự chạy `init_db.py` rồi `seed_db.py` để tạo bản cục bộ.
