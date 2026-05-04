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
python src/scripts/db_init.py
```
Creates `news.db` with standard schema. ⚠️ **Do not commit this file to the repository** — each developer seeds their local copy.

### 5. Train the Clickbait Model (One-time Setup)
```bash
python src/models/train_clickbait.py
```
Downloads and fine-tunes PhoBERT on the ViClickbait dataset (~5–15 minutes depending on hardware).  
The trained model is stored in `results/models/phobert_clickbait/` and loaded automatically in subsequent runs.

### 6. Populate Initial Data
```bash
python src/scripts/crawl_all.py
```
Crawls articles from all sources, deduplicates, and applies the trained classifier. Creates a baseline of data for the dashboard.

Or using the unified CLI:
```bash
python main.py crawl-all
```

### 6.1 Choose the Right Crawl Mode

- Full baseline crawl (first setup or major refresh):
    ```bash
    python main.py crawl-all
    ```
- Fast incremental crawl (hourly/new-only):
    ```bash
    python main.py crawl-hourly
    ```
- Selective crawl (source/category/limit):
    ```bash
    python main.py seed --source vnexpress --category kinh-doanh --limit 50
    ```

### 7. Launch the Dashboard
```bash
python main.py run
# or directly:
streamlit run src/dashboard.py
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

