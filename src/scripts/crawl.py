#!/usr/bin/env python3
"""Unified crawl entrypoint for full and hourly modes."""

from __future__ import annotations

import argparse
import os
import sys

# Ensure project root (parent of `src`) is on sys.path.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.workflows import run_crawl


def main() -> None:
    parser = argparse.ArgumentParser(description="Run crawl pipeline.")
    parser.add_argument(
        "--mode",
        choices=["full", "hourly"],
        default="full",
        help="Crawl mode: full (all) or hourly (incremental).",
    )
    parser.add_argument(
        "--max-articles",
        type=int,
        default=10,
        help="Max articles/category for hourly mode (default: 10).",
    )
    parser.add_argument(
        "--no-stop-on-duplicate",
        action="store_true",
        help="In hourly mode, continue crawling category even after duplicate.",
    )
    parser.add_argument(
        "--no-label",
        action="store_true",
        help="Skip auto labeling after crawl.",
    )
    parser.add_argument(
        "--model-path",
        default=None,
        help="Optional model path for labeling.",
    )
    parser.add_argument(
        "--model-version",
        default="phobert_v1.0",
        help="Model version string saved in predictions.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Labeling batch size.",
    )
    args = parser.parse_args()

    run_crawl(
        mode=args.mode,
        max_articles=args.max_articles,
        stop_on_duplicate=not args.no_stop_on_duplicate,
        run_label_after=not args.no_label,
        model_path=args.model_path,
        model_version=args.model_version,
        batch_size=args.batch_size,
    )


if __name__ == "__main__":
    main()
