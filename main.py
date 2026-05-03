#!/usr/bin/env python3
"""main.py - small CLI to run project tasks (init DB, run dashboard)

Usage:
  python main.py run           # runs the Streamlit dashboard
  python main.py initdb        # initializes the SQLite DB
  python main.py menu          # interactive menu
"""
import argparse
import subprocess
import sys
import os


ROOT = os.path.dirname(os.path.abspath(__file__))


def run_streamlit(port: int = 8501):
    """Run the Streamlit dashboard using the current Python interpreter."""
    cmd = [sys.executable, "-m", "streamlit", "run", "dashboard.py", "--server.address", "127.0.0.1", "--server.port", str(port)]
    print("Starting Streamlit:\n  " + " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT)


def init_db(db_path: str | None = None):
    """Run the project DB initializer script."""
    script = os.path.join(ROOT, "scripts", "init_db.py")
    cmd = [sys.executable, script]
    if db_path:
        cmd += ["--db-path", db_path]
    print("Initializing DB with:\n  " + " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT)


def interactive_menu():
    while True:
        print("\nai-news-content-analysis - Main Menu")
        print("1) Run Streamlit dashboard (localhost:8501)")
        print("2) Initialize / reset database")
        print("3) Exit")
        choice = input("Choose an option: ").strip()
        if choice == "1":
            run_streamlit()
        elif choice == "2":
            confirm = input("This will ensure DB schema exists. Continue? [y/N]: ")
            if confirm.lower().startswith("y"):
                init_db()
        elif choice == "3":
            print("Bye")
            return
        else:
            print("Unknown choice")


def main():
    parser = argparse.ArgumentParser(description="Project helper CLI")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("run", help="Run Streamlit dashboard on localhost:8501")
    sub.add_parser("initdb", help="Initialize the SQLite DB using scripts/init_db.py")
    sub.add_parser("menu", help="Interactive menu")

    parser.add_argument("--port", type=int, default=8501, help="Port for Streamlit (default 8501)")

    args = parser.parse_args()

    if args.cmd == "run":
        run_streamlit(port=args.port)
    elif args.cmd == "initdb":
        init_db()
    else:
        interactive_menu()


if __name__ == "__main__":
    main()
