# AI-Powered Vietnamese News Analysis & Clickbait Detection

Real-time web mining, topic modeling, and automated clickbait detection for Vietnamese news articles.

> **Reference:** https://www.sciencedirect.com/science/article/pii/S2352340925008856

## Overview

This project implements an end-to-end pipeline for:
- **Automated Data Collection**: Continuous crawling of Vietnamese news from multiple sources
- **Text Normalization**: HTML cleanup, deduplication, and Vietnamese text standardization
- **Clickbait Detection**: PhoBERT-based classification to identify misleading headlines
- **Topic Modeling**: BERTopic clustering to surface trending topics across timeframes
- **Interactive Dashboard**: Real-time Streamlit UI to explore articles and analytics

**Tech Stack**: Python 3.10+, PyTorch, PhoBERT, BERTopic, SQLAlchemy, SQLite, Streamlit

---

## Quick Start (5 Minutes)

### 1. Clone & Setup
```bash
git clone https://github.com/Jade2308/ai-news-content-analysis.git
cd ai-news-content-analysis
```

### 2. Virtual Environment

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

### 3. Install & Initialize
```bash
pip install -r requirements.txt
python main.py initdb
```

### 4. Train Model (One-time, ~5–15 min)
```bash
python src/models/train_clickbait.py
```
Downloads PhoBERT and fine-tunes on ViClickbait dataset. Saves to `results/models/phobert_clickbait/`.

### 5. Populate Data
```bash
python main.py crawl-all
```
Crawls articles, applies classification and topic modeling.

### 6. Launch Dashboard
```bash
python main.py run
```
Opens at `http://localhost:8501`

---

## Prerequisites

- **Python** ≥ 3.10
- **RAM** ≥ 4GB (PhoBERT model loading)
- **Storage** ≥ 2GB (database + models)
- **Internet** (for crawling and model downloads)
- **Optional**: CUDA-capable GPU for faster inference

---

## CLI Commands

```bash
# Database
python main.py initdb                    # Initialize schema
python main.py db-check                  # Verify integrity
python main.py db-query                  # Query builder

# Crawling
python main.py crawl-all                 # Full baseline crawl
python main.py crawl-hourly              # Incremental crawl
python main.py seed --source vnexpress --limit 50  # Selective crawl

# Models & Topics
python src/models/train_clickbait.py    # Train classifier
python main.py label --show-samples      # Run inference
python main.py topics --hours 24         # Topic analysis

# Dashboard
python main.py run [--port 8501]        # Launch dashboard
python main.py scheduler                 # Background jobs
```

---

## Project Structure

```
src/
├── core/              # NLP: text cleaning, topic modeling
├── crawlers/          # Scrapers: VNExpress, Tuổi Trẻ, Báo Mới, Vietnam+
├── database/          # SQLAlchemy ORM models & queries
├── models/            # PhoBERT training & inference
├── scripts/           # Executable workflows
├── streamlit/         # Streamlit dashboard UI
└── tests/             # Utilities & diagnostics

data/
├── clickbait_dataset_vietnamese.csv
├── discovered_categories.json
└── news.db (local, gitignored)

results/
├── evaluation_results/
└── models/phobert_clickbait/  (trained model)
```

---

## Core Components

| Component | Purpose |
|-----------|---------|
| **Crawlers** (`src/crawlers/`) | Extract articles from 4 Vietnamese news sources |
| **Text Processing** (`src/core/clean_text.py`) | HTML cleanup, Vietnamese normalization, deduplication |
| **Database** (`src/database/`) | SQLAlchemy ORM for articles, predictions, topics |
| **Classifier** (`src/models/phobert_classifier.py`) | PhoBERT binary classifier (Clickbait/Legitimate) |
| **Topic Modeling** (`src/core/topic_bertopic.py`) | BERTopic clustering for trend discovery |
| **Dashboard** (`src/streamlit/dashboard.py`) | Article explorer, statistics, visualizations |

---

## Data Pipeline

```
Crawlers → Clean Text → Deduplication → Classification → Topic Modeling → Database → Dashboard
```

1. **Crawl**: Extract from news sources
2. **Clean**: Normalize Vietnamese text, remove HTML
3. **Dedupe**: Remove redundant articles
4. **Classify**: PhoBERT clickbait detection
5. **Topics**: BERTopic clustering
6. **Store**: SQLite persistence
7. **Visualize**: Streamlit interface

---

## Configuration

### Environment Variables (`.env`)
```env
DB_PATH=data/news.db
STREAMLIT_PORT=8501
MODEL_PATH=results/models/phobert_clickbait
CRAWL_TIMEOUT=30
CRAWL_RETRIES=3
```

### Customize
- **Crawlers**: Edit `src/crawlers/*.py` (headers, rate limits, categories)
- **Models**: Modify `src/models/train_clickbait.py` (batch size, epochs, learning rate)
- **Topics**: Adjust `src/core/topic_bertopic.py` (tokenization, clustering params)

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Model download fails | Manually download from Hugging Face: `git clone https://huggingface.co/NlpHUST/phobert-base` |
| Database lock error | Kill existing Python processes: `taskkill /IM python.exe /F` (Windows) or `pkill -f python` (macOS/Linux) |
| Out of memory | Reduce batch size in `src/models/train_clickbait.py`: `BATCH_SIZE = 8` |
| Crawler timeouts | Increase timeout: `CRAWL_TIMEOUT = 60` in crawler config |
| Dashboard won't load | Try different port: `python main.py run --port 8502` |

---

## Development

### Add New Crawler
1. Create `src/crawlers/mynewscrawler.py`
2. Inherit from `BaseCrawler`
3. Implement `get_articles()` method
4. Register in `crawl_all.py`

### Run Tests
```bash
python src/tests/db_status.py        # Database check
python src/tests/stats_check.py      # Statistics verify
python src/tests/dashboard_test.py   # Dashboard components
```

### Retrain Model
```bash
python src/models/train_clickbait.py --epochs 5 --batch-size 32
```

---

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Commit: `git commit -m 'Add feature'`
4. Push: `git push origin feature/my-feature`
5. Open Pull Request

**Code Style**: PEP 8, type hints, docstrings, unit tests

---

## Citation

```bibtex
@article{vietnamese-clickbait-2025,
  author = {Jade, et al.},
  title = {Vietnamese News Clickbait Detection and Topic Modeling},
  url = {https://www.sciencedirect.com/science/article/pii/S2352340925008856},
  year = {2025}
}
```

**References**: PhoBERT (Pham et al., 2021) | BERTopic (Grootendorst, 2022) | ViClickbait Dataset

**License**: MIT | **Status**: Active Development | **Last Updated**: May 2026
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
| `src/database/` | SQLite schema, migrations, and query helpers |
| `src/core/` | Core types and utilities, including text cleaning and topic modeling |
| `models/` | PhoBERT clickbait classifier and evaluation utilities |
| `src/scripts/` | Orchestration tasks (crawl, label, detect topics, scheduler) |
| `src/streamlit/` | Streamlit dashboard UI application |
| `src/tests/` | Test and check utilities |
| `main.py` | CLI launcher for common tasks |

---

## Running Individual Tasks

### Label Unlabeled Articles (Inference)
Apply the trained PhoBERT model to any articles missing predictions:
```bash
python src/scripts/pred_label.py
```

Or via `main.py`:
```bash
python main.py label --show-samples
```

### Detect Hot Topics
Run topic clustering for a single timeframe (e.g., 24 hours):
```bash
python src/scripts/topic_detect.py
```

Or via `main.py`:
```bash
python main.py topics --hours 24 --top-n 10
```

### Batch Topic Detection Across All Timeframes
Compute hot topics for 1h, 6h, 12h, 24h, and 7d windows:
```bash
python src/scripts/topic_run_timeframes.py
```

Or via `main.py`:
```bash
python main.py topics-all
```

### Discover New Categories
Crawl and extract potential news categories from article metadata:
```bash
python src/scripts/topic_discover.py
```

### Automated Background Scheduler
Run continuous crawling, classification, and topic detection (every 60 minutes):
```bash
python src/scripts/sched_run.py
```
Recommended daemon entrypoint via `main.py`:
```bash
python main.py scheduler
```
This command launches a background process that:
1. Crawls new articles
2. Removes duplicates
3. Applies PhoBERT classifier
4. Runs topic clustering
5. Waits 60 minutes and repeats

---

## Dashboard Features

The Streamlit dashboard (`src/streamlit/dashboard.py`) provides:
- **Dark Theme UI** with modern card layouts
- **Article Feed**: Browse recent articles with real-time predictions
- **Hot Topics View**: See trending topics across different timeframes (1h, 6h, 24h, 1 week)
- **Clickbait Stats**: Overview of classification results (counts, confidence scores)
- **Search Page**: Full-text search across title and summary
- **Article Detail Page**: Read full content with source and prediction badges

Access the dashboard after running step 7 above.

---

## Command-Line Interface (CLI)

The `main.py` script provides a unified CLI for core workflows:

```bash
# Run the dashboard on localhost:8501
python main.py run

# Initialize the database
python main.py initdb

# Full crawl (all configured sources/categories)
python main.py crawl-all

# Incremental crawl (new articles only)
python main.py crawl-hourly

# Selective crawl
python main.py seed --source all --limit 50

# Label unlabeled articles with the clickbait model
python main.py label --model-path results/models/phobert_clickbait --batch-size 32

# Detect topics for one timeframe
python main.py topics --hours 24 --top-n 10

# Detect topics for all timeframes (1h/6h/12h/24h/168h)
python main.py topics-all

# Run scheduler daemon (hourly automation)
python main.py scheduler

# DB health and DB statistics
python main.py db-check
python main.py db-query

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
- **Location**: `results/models/phobert_clickbait/`
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
├── src/                           # Main source code
│   ├── crawlers/                  # Web scraping modules
│   ├── core/                      # Core types and utilities
│   ├── config.py                  # Global configuration
│   ├── streamlit/                 # Streamlit UI
│   └── tests/                     # Test and check utilities
├── data/                          # Data artifacts
│   ├── clickbait_dataset_vietnamese.csv
│   ├── discovered_categories.json
│   └── news.db                    # SQLite database (local only, not committed)
├── src/database/                  # SQLite schema, query helpers, migrations
├── results/                       # Models and evaluation results
│   ├── models/                    # AI models (clickbait classifier)
│   │   └── phobert_clickbait/    # PhoBERT fine-tuned model
│   └── evaluation_results/        # Model evaluation metrics
├── src/scripts/                   # Automation and utility scripts
│   ├── crawl_all.py               # Full crawl pipeline
│   ├── crawl_hourly.py            # Hourly incremental crawl
│   ├── db_init.py                 # Database initialization
│   ├── db_seed.py                 # Database seeding
│   ├── model_list.py              # Model listing utility
│   ├── pred_label.py              # Prediction/labeling
│   ├── query_articles.py          # Article querying
│   ├── sched_config.py            # Scheduler configuration
│   ├── sched_run.py               # Scheduler runner
│   ├── topic_detect.py            # Topic detection
│   ├── topic_discover.py          # Category discovery
│   └── topic_run_timeframes.py    # Multi-timeframe topic analysis
├── src/tests/                     # Test and check utilities
│   ├── dashboard_test.py          # Dashboard tests
│   ├── dates_check.py             # Date utility checks
│   ├── db_status.py               # Database status check
│   ├── stats_check.py             # Statistics checks
│   └── stats_debug.py             # Debug statistics
├── main.py                        # CLI launcher
├── requirements.txt               # Python dependencies
├── README.md                      # This file
├── .gitignore                     # Git exclusion rules
└── .venv/                         # Virtual environment (local, not committed)
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

