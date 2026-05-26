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
from pathlib import Path
from dotenv import load_dotenv

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

TOP_ICON = "◆"
SECTION_ICON = "▣"
ITEM_ICON = "▸"
ACTION_ICON = "➤"


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
    print(style(f"\n{TOP_ICON} {title}", CYAN, bold=True))


def print_section(title: str, color: str):
    print(style(f"\n{SECTION_ICON} {title}", color, bold=True))


def print_option(number: int | str, label: str, color: str = WHITE, icon: str = ITEM_ICON):
    print(style(f"  {icon} {number}. {label}", color))


def run_python_script(script_name: str, args: list[str] | None = None):
    """Run a project script with the active interpreter from project root."""
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)

    print("Running:\n  " + " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT)


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


def run_streamlit(port: int = 8501):
    """Run the Streamlit dashboard using the current Python interpreter."""
    dashboard_path = os.path.join(ROOT, "src", "streamlit", "streamlit.py")
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
    run_python_script("db_init.py", args)


def crawl_all():
    run_python_script("crawl.py", ["--mode", "full"])


def crawl_hourly():
    run_python_script("crawl.py", ["--mode", "hourly"])


def seed_data(source: str, category: str | None, limit: int, db_path: str | None):
    args = ["--source", source, "--limit", str(limit)]
    if category:
        args.extend(["--category", category])
    if db_path:
        args.extend(["--db-path", db_path])
    run_python_script("db_seed.py", args)


def label_articles(model_path: str | None, model_version: str, batch_size: int, show_samples: bool):
    resolved_model_path = resolve_model_path(model_path)
    if not resolved_model_path:
        print("ERROR: no trained clickbait model found.")
        print("Expected a model folder containing config + weights, e.g.:")
        print("  - results/models/phobert_clickbait/model.safetensors")
        print("Train first with:")
        print('  python src/models/train_clickbait.py --output-dir "results/models/phobert_clickbait"')
        return

    args = [
        "--model-path", resolved_model_path,
        "--model-version", model_version,
        "--batch-size", str(batch_size),
    ]
    if show_samples:
        args.append("--show-samples")
    run_python_script("pred_label.py", args)


def detect_topics(hours: int, top_n: int):
    if not os.getenv("GEMINI_API_KEY"):
        print("Info: GEMINI_API_KEY is not set. Topic naming will use keyword fallback.")
    run_python_script("topic_detect.py", ["--hours", str(hours), "--top_n", str(top_n)])


def detect_topics_all_timeframes():
    if not os.getenv("GEMINI_API_KEY"):
        print("Info: GEMINI_API_KEY is not set. Topic naming will use keyword fallback.")
    run_python_script("topic_detect.py", ["--all-timeframes"])


def run_scheduler_daemon():
    run_python_script("sched_run.py")


def check_db():
    run_python_script("db_tools.py", ["check"])


def query_db():
    run_python_script("db_tools.py", ["stats"])


def clean_db(days: int):
    run_python_script("db_clean.py", ["--days", str(days)])


def interactive_menu():
    while True:
        try:
            print_header("AI News Content Analysis")
            print(style("  Choose an action. Press Ctrl+C to exit safely.", DIM))

            print_section("Core", CYAN)
            print_option(1, "Run Streamlit dashboard (localhost:8501)", WHITE, icon=ACTION_ICON)
            print_option(2, "Single-run pipeline (crawl -> label -> topics)", MAGENTA, icon=ACTION_ICON)
            print_option(3, "Run scheduler daemon", MAGENTA, icon=ACTION_ICON)
            print(style("  * Hint: press Ctrl+C in this terminal to stop Streamlit.", DIM))

            print_section("Database", BLUE)
            print_option(4, "Initialize / reset database", WHITE)
            print_option(5, "Check database status", WHITE)
            print_option(6, "Query database statistics", WHITE)
            print_option(7, "Clean old database data", WHITE)

            print_section("Crawling", GREEN)
            print_option(8, "Crawl all newspapers (full)", WHITE)
            print_option(9, "Crawl hourly (incremental)", WHITE)
            print_option(10, "Selective crawl (source/category)", WHITE)

            print_section("AI Analysis", YELLOW)
            print_option(11, "Label unpredicted articles", WHITE)
            print_option(12, "Detect hot topics (single timeframe)", WHITE)
            print_option(13, "Detect hot topics (all timeframes)", WHITE)

            print_section("More", MAGENTA)
            print_option(14, "Automation submenu (legacy)", WHITE)
            print_option(0, "Exit", RED, icon=ACTION_ICON)

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
            port_raw = input("Dashboard port (default 8501): ").strip() or "8501"
            try:
                port = int(port_raw)
            except ValueError:
                print(style("Invalid port, using 8501", YELLOW))
                port = 8501
            run_streamlit(port=port)
        elif choice == "2":
            run_single_automation()
        elif choice == "3":
            run_scheduler_daemon()
        elif choice == "4":
            confirm = input("This will ensure DB schema exists. Continue? [y/N]: ")
            if confirm.lower().startswith("y"):
                init_db()
        elif choice == "5":
            check_db()
        elif choice == "6":
            query_db()
        elif choice == "7":
            days_raw = input("Days window to keep (default 14): ").strip() or "14"
            try:
                days = int(days_raw)
            except ValueError:
                print(style("Invalid number, using 14", YELLOW))
                days = 14
            clean_db(days=days)
        elif choice == "8":
            crawl_all()
        elif choice == "9":
            crawl_hourly()
        elif choice == "10":
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
        elif choice == "11":
            model_path = None
            print("Using auto-detected model path (no manual path input required).")
            model_version = input("Model version (default phobert_v1.0): ").strip() or "phobert_v1.0"
            batch_raw = input("Batch size (default 32): ").strip() or "32"
            show_samples = input("Show sample predictions? [y/N]: ").strip().lower().startswith("y")
            try:
                batch_size = int(batch_raw)
            except ValueError:
                print(style("Invalid batch size, using 32", YELLOW))
                batch_size = 32
            label_articles(model_path, model_version, batch_size, show_samples)
        elif choice == "12":
            hours_raw = input("Hours window (default 24): ").strip() or "24"
            top_n_raw = input("Top topics (default 10): ").strip() or "10"
            try:
                hours = int(hours_raw)
                top_n = int(top_n_raw)
            except ValueError:
                print(style("Invalid numbers, using hours=24, top_n=10", YELLOW))
                hours, top_n = 24, 10
            detect_topics(hours=hours, top_n=top_n)
        elif choice == "13":
            detect_topics_all_timeframes()
        elif choice == "14":
            automation_menu()
        else:
            print(style("Unknown choice", RED, bold=True))


def automation_menu():
    """Simple automation submenu: single-run pipeline or scheduler."""
    while True:
        print_header("Automation Menu")
        print_option(0, "Back", RED, icon=ACTION_ICON)
        print_option(1, "Single-run automation (crawl -> label -> topics)", MAGENTA)
        print_option(2, "Run scheduler daemon", MAGENTA)
        choice = input("Choose an option: ").strip()

        if choice == "0":
            return
        if choice == "1":
            run_single_automation()
        elif choice == "2":
            run_scheduler_daemon()
        else:
            print(style("Unknown choice", RED, bold=True))


def run_single_automation():
    """Run a one-shot automation pipeline: crawl -> label -> detect topics."""
    print("\nSingle-run automation: crawl -> label -> topics")
    crawl_type = input("Crawl type [full|selective] (default full): ").strip() or "full"
    if crawl_type == "selective":
        source = input("Source [vnexpress|tuoitre|vietnamnet|all] (default all): ").strip() or "all"
        category = input("Category (optional): ").strip() or None
        limit_raw = input("Limit per source/category (default 50): ").strip() or "50"
        try:
            limit = int(limit_raw)
        except ValueError:
            print("Invalid limit, using 50")
            limit = 50
        seed_data(source=source, category=category, limit=limit, db_path=None)
    else:
        crawl_all()

    # Labeling
    print("\nNext: labeling step")
    model_path = None
    print("Using auto-detected model path (no manual path input required).")
    model_version = input("Model version (default phobert_v1.0): ").strip() or "phobert_v1.0"
    batch_raw = input("Batch size (default 32): ").strip() or "32"
    show_samples = input("Show sample predictions? [y/N]: ").strip().lower().startswith("y")
    try:
        batch_size = int(batch_raw)
    except ValueError:
        print("Invalid batch size, using 32")
        batch_size = 32
    label_articles(model_path, model_version, batch_size, show_samples)

    # Topics detection
    print("\nNext: detect topics")
    hours_raw = input("Hours window (default 24): ").strip() or "24"
    top_n_raw = input("Top topics (default 10): ").strip() or "10"
    try:
        hours = int(hours_raw)
        top_n = int(top_n_raw)
    except ValueError:
        print("Invalid numbers, using hours=24, top_n=10")
        hours, top_n = 24, 10
    detect_topics(hours=hours, top_n=top_n)


def main():
    parser = argparse.ArgumentParser(description="Project helper CLI")
    sub = parser.add_subparsers(dest="cmd")

    run_parser = sub.add_parser("run", help="Run Streamlit dashboard on localhost:8501")
    run_parser.add_argument("--port", type=int, default=8501, help="Port for Streamlit (default 8501)")

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
            run_streamlit(port=args.port)
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

