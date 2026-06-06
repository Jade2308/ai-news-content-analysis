#!/usr/bin/env python3
"""main.py - project task launcher for core workflows.

Usage examples:
    python main.py run --port 8501
    python main.py initdb
    python main.py crawl-all
    python main.py crawl-hourly
    python main.py seed --source vnexpress --category kinh-doanh --limit 30
    python main.py label --show-samples
    python main.py topics --hours 24 --top-n 10
    python main.py topics-all
    python main.py scheduler
    python main.py db-check
    python main.py db-query
"""
import argparse
import subprocess
import sys
import os
import socket
import sqlite3
from pathlib import Path
from dotenv import load_dotenv
from src.config import DB_PATH

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()


ROOT = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(ROOT, "src", "scripts")
DEFAULT_MODEL_PATH = os.path.join("results", "models", "phobert_clickbait")

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"
RED = "\033[31m"
WHITE = "\033[37m"

def style(text: str, color: str = "", bold: bool = False, dim: bool = False) -> str:
    parts = []
    if bold:
        parts.append(BOLD)
    if dim:
        parts.append(DIM)
    if color:
        parts.append(color)
    parts.append(text)
    parts.append(RESET)
    return "".join(parts)


def print_header(title: str):
    print(style(f"\n{title}", bold=True))


def print_section(title: str, color: str):
    print(style(f"\n{title}", bold=True))


def print_option(number: int | str, label: str, color: str = ""):
    print(style(f"  {number}. {label}", color))


def run_python_script(script_name: str, args: list[str] | None = None):
    """Run a project script with the active interpreter from project root."""
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)

    print("Running:\n  " + " ".join(cmd))
    return subprocess.run(cmd, cwd=ROOT)


def _is_trained_model_dir(path: Path) -> bool:
    """Return True if *path* looks like a trained HuggingFace model directory."""
    if not path.exists() or not path.is_dir():
        return False
    if not (path / "config.json").exists():
        return False
    weight_files = ["model.safetensors", "pytorch_model.bin", "tf_model.h5"]
    return any((path / name).exists() for name in weight_files)


def resolve_model_path(preferred: str | None = None) -> str | None:
    """Resolve a usable trained model directory with sane defaults."""
    candidates: list[str] = []
    if preferred:
        candidates.append(preferred)
    candidates.extend([
        os.path.join("results", "models", "phobert_clickbait"),
        os.path.join("results", "models", "visobert_clickbait"),
        os.path.join("results", "models", "xlm_roberta_clickbait"),
        os.path.join("models", "phobert_clickbait"),
    ])

    for relative in candidates:
        if _is_trained_model_dir(Path(ROOT, relative)):
            return relative

    return None


def get_article_count() -> int:
    """Return total article rows from the SQLite database."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            row = conn.execute("SELECT COUNT(*) FROM articles").fetchone()
            return int(row[0]) if row else 0
    except Exception:
        return 0


def get_labeled_article_count() -> int:
    """Return number of labeled articles in the SQLite database."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            row = conn.execute("SELECT COUNT(*) FROM articles WHERE predicted_label IS NOT NULL").fetchone()
            return int(row[0]) if row else 0
    except Exception:
        return 0


def train_model_if_needed(output_dir: str = DEFAULT_MODEL_PATH) -> bool:
    """Train a clickbait model only when no trained model is available."""
    existing_model = resolve_model_path(preferred=output_dir)
    if existing_model:
        print(style(f"Model ready: {existing_model}", GREEN))
        return True

    dataset_path = Path(ROOT, "data", "clickbait_vietnamese_dataset.csv")
    if not dataset_path.exists():
        print(style("ERROR: dataset not found for training:", RED, bold=True))
        print(f"  {dataset_path}")
        return False

    train_script = os.path.join(ROOT, "src", "models", "train_clickbait.py")
    cmd = [sys.executable, train_script, "--output-dir", output_dir]
    print(style("No trained model found. Training model now...", YELLOW, bold=True))
    print("Running:\n  " + " ".join(cmd))
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        print(style("ERROR: model training failed.", RED, bold=True))
        return False

    trained_model = resolve_model_path(preferred=output_dir)
    if not trained_model:
        print(style("ERROR: training finished but no model weights were found.", RED, bold=True))
        return False

    print(style(f"Training completed. Model ready: {trained_model}", GREEN))
    return True


def find_available_port(start_port: int = 8501, host: str = "127.0.0.1", max_tries: int = 100) -> int:
    """Find the first available TCP port, starting from start_port."""
    for port in range(start_port, start_port + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"No available port found in range {start_port}-{start_port + max_tries - 1}.")


def run_streamlit(start_port: int = 8501):
    """Run the Streamlit dashboard using the current Python interpreter."""
    dashboard_path = os.path.join(ROOT, "src", "streamlit", "streamlit.py")
    port = find_available_port(start_port=start_port)
    if port != start_port:
        print(style(f"Port {start_port} is busy. Using {port} instead.", YELLOW))
    cmd = [sys.executable, "-m", "streamlit", "run", dashboard_path, "--server.address", "127.0.0.1", "--server.port", str(port)]
    print("Starting Streamlit:\n  " + " ".join(cmd))
    print("Press Ctrl+C to stop the server cleanly.")
    # Use Popen so we can handle KeyboardInterrupt and terminate child process cleanly
    proc = subprocess.Popen(cmd, cwd=ROOT)
    try:
        proc.wait()
    except KeyboardInterrupt:
        print("Stopping Streamlit (KeyboardInterrupt received)...")
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
        print("Streamlit stopped.")


def init_db(db_path: str | None = None):
    """Run database initializer."""
    args: list[str] = []
    if db_path:
        args.extend(["--db-path", db_path])
    return run_python_script("db_init.py", args)


def crawl_all():
    return run_python_script("crawl.py", ["--mode", "full"])


def crawl_hourly():
    return run_python_script("crawl.py", ["--mode", "hourly"])


def seed_data(source: str, category: str | None, limit: int, db_path: str | None):
    args = ["--source", source, "--limit", str(limit)]
    if category:
        args.extend(["--category", category])
    if db_path:
        args.extend(["--db-path", db_path])
    return run_python_script("db_seed.py", args)


def label_articles(model_path: str | None, model_version: str, batch_size: int, show_samples: bool):
    resolved_model_path = resolve_model_path(model_path)
    if not resolved_model_path:
        print("ERROR: no trained clickbait model found.")
        print("Expected a model folder containing config + weights, e.g.:")
        print("  - results/models/phobert_clickbait/model.safetensors")
        print("Train first with:")
        print('  python src/models/train_clickbait.py --output-dir "results/models/phobert_clickbait"')
        return False

    args = [
        "--model-path", resolved_model_path,
        "--model-version", model_version,
        "--batch-size", str(batch_size),
    ]
    if show_samples:
        args.append("--show-samples")
    result = run_python_script("pred_label.py", args)
    return result.returncode == 0


def detect_topics(hours: int, top_n: int):
    result = run_python_script("topic_detect.py", ["--hours", str(hours), "--top_n", str(top_n)])
    return result.returncode == 0


def detect_topics_all_timeframes():
    result = run_python_script("topic_detect.py", ["--all-timeframes"])
    return result.returncode == 0


def run_scheduler_daemon():
    return run_python_script("sched_run.py")


def check_db():
    return run_python_script("db_tools.py", ["check"])


def query_db():
    return run_python_script("db_tools.py", ["stats"])


def clean_db(days: int):
    return run_python_script("db_clean.py", ["--days", str(days)])


def interactive_menu():
    def print_menu() -> None:
        article_count = get_article_count()
        labeled_count = get_labeled_article_count()
        model_path = resolve_model_path()
        model_status = model_path if model_path else "not trained"

        print_header("AI News Content Analysis")
        print(style("  Fast command center (max 10 options). Press Ctrl+C to exit.", DIM))
        print(style(f"  DB: {article_count} articles | labeled: {labeled_count}", DIM))
        print(style(f"  Model: {model_status}", DIM))
        print("\nMain Actions")
        print_option(1, "Launch Streamlit dashboard")
        print_option(2, "Run full auto workflow")
        print_option(3, "Crawl all newspapers (full)")
        print_option(4, "Crawl hourly updates")
        print_option(5, "Selective crawl (source/category)")
        print_option(6, "Label unlabeled articles (local model)")
        print_option(7, "Detect hot topics")
        print_option(8, "Database tools")
        print_option(9, "Run scheduler daemon")
        print_option(0, "Exit")

    while True:
        try:
            print_menu()
            choice = input("Choose an option: ").strip()
        except KeyboardInterrupt:
            print()
            print(style("Interrupted. Exiting menu.", GREEN, bold=True))
            return
        except EOFError:
            print()
            print(style("Input closed. Exiting menu.", GREEN, bold=True))
            return

        if choice == "0":
            print(style("Bye", GREEN, bold=True))
            return
        if choice == "1":
            run_streamlit()
        elif choice == "2":
            run_single_automation()
        elif choice == "3":
            crawl_all()
        elif choice == "4":
            crawl_hourly()
        elif choice == "5":
            source = input("Source [vnexpress|tuoitre|vietnamnet|all] (default all): ").strip() or "all"
            category = input("Category (optional): ").strip() or None
            limit_raw = input("Limit per source/category (default 50): ").strip() or "50"
            db_path = input("Custom DB path (optional): ").strip() or None
            try:
                limit = int(limit_raw)
            except ValueError:
                print(style("Invalid limit, using 50", YELLOW))
                limit = 50
            seed_data(source=source, category=category, limit=limit, db_path=db_path)
        elif choice == "6":
            print("Using auto-detected model path (no manual path input required).")
            model_version = input("Model version (default phobert_v1.0): ").strip() or "phobert_v1.0"
            batch_raw = input("Batch size (default 32): ").strip() or "32"
            show_samples = input("Show sample predictions? [y/N]: ").strip().lower().startswith("y")
            try:
                batch_size = int(batch_raw)
            except ValueError:
                print(style("Invalid batch size, using 32", YELLOW))
                batch_size = 32
            label_articles(model_path=None, model_version=model_version, batch_size=batch_size, show_samples=show_samples)
        elif choice == "7":
            mode = input("Topic mode [1=single timeframe, 2=all timeframes] (default 1): ").strip() or "1"
            if mode == "2":
                detect_topics_all_timeframes()
            else:
                hours_raw = input("Hours window (default 24): ").strip() or "24"
                top_n_raw = input("Top topics (default 10): ").strip() or "10"
                try:
                    hours = int(hours_raw)
                    top_n = int(top_n_raw)
                except ValueError:
                    print(style("Invalid numbers, using hours=24, top_n=10", YELLOW))
                    hours, top_n = 24, 10
                detect_topics(hours=hours, top_n=top_n)
        elif choice == "8":
            print_section("Database Tools", BLUE)
            print_option("a", "Initialize DB schema", WHITE)
            print_option("b", "Health check", WHITE)
            print_option("c", "Query statistics", WHITE)
            print_option("d", "Clean old data", WHITE)
            db_choice = input("Choose [a/b/c/d] (or Enter to cancel): ").strip().lower()
            if db_choice == "a":
                confirm = input("This will ensure DB schema exists. Continue? [y/N]: ")
                if confirm.lower().startswith("y"):
                    init_db()
            elif db_choice == "b":
                check_db()
            elif db_choice == "c":
                query_db()
            elif db_choice == "d":
                days_raw = input("Days window to keep (default 14): ").strip() or "14"
                try:
                    days = int(days_raw)
                except ValueError:
                    print(style("Invalid number, using 14", YELLOW))
                    days = 14
                clean_db(days=days)
        elif choice == "9":
            run_scheduler_daemon()
        else:
            print(style("Unknown choice", RED, bold=True))


def run_auto_workflow(
    launch_dashboard: bool = True,
    model_version: str = "phobert_v1.0",
    batch_size: int = 32,
    topic_hours: int = 24,
    topic_top_n: int = 10,
) -> bool:
    """Run auto workflow: init DB -> crawl if empty -> train if missing -> label -> topics -> optional dashboard."""
    print_header("Auto Workflow")
    tail = " -> dashboard" if launch_dashboard else ""
    print(style(f"Running: init DB -> crawl(if empty) -> train(if missing) -> label -> topics{tail}", DIM))

    # 1) Ensure database schema exists
    init_result = init_db()
    if init_result.returncode != 0:
        print(style("Database initialization failed. Stopping workflow.", RED, bold=True))
        return False

    # 2) Crawl only when there are no articles
    existing_articles = get_article_count()
    if existing_articles <= 0:
        print(style("No articles found. Starting full crawl...", YELLOW, bold=True))
        crawl_result = crawl_all()
        if crawl_result.returncode != 0:
            print(style("Crawl failed. Stopping workflow.", RED, bold=True))
            return False
    else:
        print(style(f"Articles already available ({existing_articles}). Skipping crawl.", GREEN))

    # 3) Train model only when no trained model exists
    if not train_model_if_needed(output_dir=DEFAULT_MODEL_PATH):
        print(style("Cannot continue without a trained model.", RED, bold=True))
        return False

    # 4) Label articles
    print(style("Running label step...", CYAN, bold=True))
    if not label_articles(model_path=None, model_version=model_version, batch_size=batch_size, show_samples=False):
        print(style("Labeling failed. Stopping workflow.", RED, bold=True))
        return False
    labeled_now = get_labeled_article_count()
    print(style(f"Labeled articles in DB: {labeled_now}", GREEN))

    # 5) Detect hot topics
    print(style(f"Running topic detection ({topic_hours}h, top {topic_top_n})...", CYAN, bold=True))
    if not detect_topics(hours=topic_hours, top_n=topic_top_n):
        print(style("Topic detection failed. Stopping workflow.", RED, bold=True))
        return False

    # 6) Optionally launch dashboard
    if launch_dashboard:
        print(style("Launching Streamlit dashboard...", MAGENTA, bold=True))
        run_streamlit()

    return True


def run_single_automation():
    """Run menu automation and launch dashboard at the end."""
    run_auto_workflow(launch_dashboard=True)


def main():
    parser = argparse.ArgumentParser(description="Project helper CLI")
    sub = parser.add_subparsers(dest="cmd")

    run_parser = sub.add_parser("run", help="Run Streamlit dashboard (auto port from 8501)")
    run_parser.add_argument("--port", type=int, default=8501, help="Starting port to try (default 8501)")

    initdb_parser = sub.add_parser("initdb", help="Initialize the SQLite DB")
    initdb_parser.add_argument("--db-path", default=None, help="Custom database path")

    sub.add_parser("crawl-all", help="Full crawl across all configured newspapers and categories")
    sub.add_parser("crawl-hourly", help="Incremental hourly crawl for new articles")

    seed_parser = sub.add_parser("seed", help="Selective crawl by source/category")
    seed_parser.add_argument("--source", choices=["vnexpress", "tuoitre", "vietnamnet", "all"], default="all")
    seed_parser.add_argument("--category", default=None)
    seed_parser.add_argument("--limit", type=int, default=50)
    seed_parser.add_argument("--db-path", default=None)

    label_parser = sub.add_parser("label", help="Predict clickbait labels for unlabeled articles")
    label_parser.add_argument("--model-path", default=None, help="Model directory path")
    label_parser.add_argument("--model-version", default="phobert_v1.0")
    label_parser.add_argument("--batch-size", type=int, default=32)
    label_parser.add_argument("--show-samples", action="store_true")

    topics_parser = sub.add_parser("topics", help="Detect hot topics for one timeframe")
    topics_parser.add_argument("--hours", type=int, default=24)
    topics_parser.add_argument("--top-n", type=int, default=10)

    auto_parser = sub.add_parser("auto", help="Run full auto workflow (crawl/train-if-needed/label/topics)")
    auto_parser.add_argument("--skip-dashboard", action="store_true", help="Do not launch Streamlit at the end")
    auto_parser.add_argument("--model-version", default="phobert_v1.0")
    auto_parser.add_argument("--batch-size", type=int, default=32)
    auto_parser.add_argument("--hours", type=int, default=24, help="Topic detection timeframe in hours")
    auto_parser.add_argument("--top-n", type=int, default=10, help="Top N topics")

    sub.add_parser("topics-all", help="Detect hot topics for 1h/6h/12h/24h/168h")
    sub.add_parser("scheduler", help="Run hourly scheduler daemon")
    sub.add_parser("db-check", help="Check database health and summary")
    sub.add_parser("db-query", help="Query and print database statistics")
    clean_parser = sub.add_parser("db-clean", help="Clean old data from database")
    clean_parser.add_argument("--days", type=int, default=14, help="Keep data from the last N days")

    try:
        args = parser.parse_args()

        if args.cmd is None:
            interactive_menu()
        elif args.cmd == "run":
            run_streamlit(start_port=args.port)
        elif args.cmd == "initdb":
            init_db(db_path=args.db_path)
        elif args.cmd == "crawl-all":
            crawl_all()
        elif args.cmd == "crawl-hourly":
            crawl_hourly()
        elif args.cmd == "seed":
            seed_data(source=args.source, category=args.category, limit=args.limit, db_path=args.db_path)
        elif args.cmd == "label":
            label_articles(
                model_path=args.model_path,
                model_version=args.model_version,
                batch_size=args.batch_size,
                show_samples=args.show_samples,
            )
        elif args.cmd == "topics":
            detect_topics(hours=args.hours, top_n=args.top_n)
        elif args.cmd == "auto":
            ok = run_auto_workflow(
                launch_dashboard=not args.skip_dashboard,
                model_version=args.model_version,
                batch_size=args.batch_size,
                topic_hours=args.hours,
                topic_top_n=args.top_n,
            )
            if not ok:
                raise SystemExit(1)
        elif args.cmd == "topics-all":
            detect_topics_all_timeframes()
        elif args.cmd == "scheduler":
            run_scheduler_daemon()
        elif args.cmd == "db-check":
            check_db()
        elif args.cmd == "db-query":
            query_db()
        elif args.cmd == "db-clean":
            clean_db(days=args.days)
        else:
            parser.print_help()
    except KeyboardInterrupt:
        print()
        print(style("Interrupted. Bye.", GREEN, bold=True))
    except EOFError:
        print()
        print(style("Input closed. Bye.", GREEN, bold=True))


if __name__ == "__main__":
    main()

