# AI News Content Analysis

Vietnamese news crawling, clickbait detection, hot-topic discovery, and dashboard analytics.

Reference paper: https://www.sciencedirect.com/science/article/pii/S2352340925008856

## What It Does
- Crawl Vietnamese news sources.
- Clean and normalize article text.
- Predict clickbait labels with transformer models.
- Detect hot topics from recent articles.
- Store data in SQLite and visualize with Streamlit.

## Prerequisites
- Python 3.10+
- `pip`

## Setup
```bash
git clone https://github.com/Jade2308/ai-news-content-analysis.git
cd ai-news-content-analysis
python -m venv .venv
```

Windows:
```powershell
.venv\Scripts\Activate.ps1
```

macOS/Linux:
```bash
source .venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Initialize database:
```bash
python main.py initdb
```

## Quick Run
1. Train model once:
```bash
python src/models/train_clickbait.py
```
2. Crawl:
```bash
python main.py crawl-all
```
3. Label new articles:
```bash
python main.py label
```
4. Detect topics:
```bash
python main.py topics --hours 24 --top-n 10
```
5. Launch dashboard:
```bash
python main.py run --port 8501
```
Open: `http://localhost:8501`

## CLI Commands
```bash
# database
python main.py initdb
python main.py db-check
python main.py db-query
python main.py db-clean --days 14

# crawling
python main.py crawl-all
python main.py crawl-hourly
python main.py seed --source all --limit 50

# labeling and topics
python main.py label --batch-size 32
python main.py topics --hours 24 --top-n 10
python main.py topics-all

# scheduler + dashboard
python main.py scheduler
python main.py run --port 8501
```

## Model Comparison
Train different backbones:
```bash
python src/models/train_clickbait.py --model-name "vinai/phobert-base" --output-dir "results/models/phobert_clickbait"
python src/models/train_clickbait.py --model-name "uitnlp/visobert" --output-dir "results/models/visobert_clickbait"
python src/models/train_clickbait.py --model-name "xlm-roberta-base" --output-dir "results/models/xlm_roberta_clickbait"
```

Evaluate:
```bash
python src/models/evaluate.py --model-path "results/models/phobert_clickbait" --output-dir "results/evaluation/phobert"
python src/models/evaluate.py --model-path "results/models/visobert_clickbait" --output-dir "results/evaluation/visobert"
python src/models/evaluate.py --model-path "results/models/xlm_roberta_clickbait" --output-dir "results/evaluation/xlm_roberta"
```

Create comparison chart:
```bash
python src/models/compare_models.py
```

## Notes
- Local database defaults to `data/news.db`.
- Topic naming can use Gemini API if `GEMINI_API_KEY` is set in `.env`.
- Scheduler runs crawling/topic pipeline hourly.

## Troubleshooting
- Missing model: run training first or pass `--model-path`.
- Empty dashboard: run `crawl-all`, then `label`, then `topics`.
- Slow runtime on small VPS: use CPU-only environment and keep hourly crawl incremental.

## License
MIT
