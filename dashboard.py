"""
AI News Dashboard
Giao diện phân tích và đọc tin tức bằng AI
"""

from __future__ import annotations

import html
import re
import sqlite3
import sys
from pathlib import Path
from typing import Sequence
from datetime import datetime

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from config import DB_PATH
from database.schema import init_db

# Page config
st.set_page_config(
	page_title="AI News Analysis",
	page_icon="📰",
	layout="wide",
	initial_sidebar_state="collapsed"
)

TIMEFRAME_OPTIONS = {
	"1 giờ": 1,
	"6 giờ": 6,
	"12 giờ": 12,
	"24 giờ": 24,
	"7 ngày": 168,
}

HOT_TOPIC_TIMEFRAME_OPTIONS = {
	"1 giờ": 1,
	"6 giờ": 6,
	"24 giờ": 24,
	"1 tuần": 168,
}

HOT_TOPIC_FEED_LIMIT = 10

LABEL_OPTIONS = [
	"Tất cả",
	"clickbait",
	"non-clickbait",
	"Chưa gán nhãn",
]

# Database functions
def ensure_database() -> None:
	init_db(DB_PATH)

@st.cache_data(ttl=3600, show_spinner=False)
def cached_read_sql(query: str, params: Sequence | None = None) -> pd.DataFrame:
	with sqlite3.connect(DB_PATH) as conn:
		return pd.read_sql_query(query, conn, params=params or ())

def uncached_read_sql(query: str, params: Sequence | None = None) -> pd.DataFrame:
	"""Read SQL without caching - for dynamic queries like stats"""
	with sqlite3.connect(DB_PATH) as conn:
		return pd.read_sql_query(query, conn, params=params or ())

@st.cache_data(ttl=3600, show_spinner=False)
def get_sqlite_sequence_value(table_name: str) -> int:
	"""Return the current AUTOINCREMENT sequence for a table."""
	df = uncached_read_sql(
		"""
		SELECT seq
		FROM sqlite_sequence
		WHERE name = ?
		LIMIT 1
		""",
		(table_name,),
	)
	if df.empty:
		return 0
	value = df.iloc[0].get("seq")
	try:
		return int(value) if value is not None else 0
	except (TypeError, ValueError):
		return 0

@st.cache_data(ttl=3600, show_spinner=False)
def get_distinct_values(column: str) -> list[str]:
	df = cached_read_sql(
		f"""
		SELECT DISTINCT {column} AS value
		FROM articles
		WHERE {column} IS NOT NULL AND TRIM({column}) != ''
		ORDER BY value
		"""
	)
	return [str(v) for v in df["value"].tolist() if v is not None]

def normalize_category_label(category: str) -> str:
	value = str(category or "").strip()
	return value if value else "Khác"


def extract_first_image_url(raw_html: str | None) -> str | None:
	"""Extract the first image src from stored HTML snippet if available."""
	if not raw_html:
		return None
	match = re.search(r"<img[^>]+src=[\"']([^\"']+)[\"']", str(raw_html), flags=re.IGNORECASE)
	if not match:
		return None
	img_url = match.group(1).strip()
	if img_url.startswith("//"):
		return f"https:{img_url}"
	if img_url.startswith("http://") or img_url.startswith("https://"):
		return img_url
	return None

def _build_article_where_clause(
	hours: int,
	source: str | None = None,
	category: str | None = None,
	label: str | None = None,
) -> tuple[str, tuple]:
	clauses = []
	params: list = []

	if hours:
		clauses.append("crawled_at >= datetime('now', '-' || ? || ' hours')")
		params.append(hours)

	if source and source != "Tất cả":
		clauses.append("source = ?")
		params.append(source)

	if category and category != "Tất cả":
		clauses.append("category = ?")
		params.append(category)

	if label and label != "Tất cả":
		if label == "Chưa gán nhãn":
			clauses.append("predicted_label IS NULL")
		else:
			clauses.append("predicted_label = ?")
			params.append(label)

	where_clause = " WHERE " + " AND ".join(clauses) if clauses else ""
	return where_clause, tuple(params)

@st.cache_data(ttl=3600, show_spinner=False)
def get_recent_articles(
	hours: int,
	source: str,
	category: str,
	label: str,
	limit: int = 500,
) -> pd.DataFrame:
	where_clause, params = _build_article_where_clause(hours, source, category, label)
	return cached_read_sql(
		f"""
		SELECT
			article_id, title, summary, content_text, source, category,
			url, predicted_label, prediction_score,
			published_at, crawled_at
		FROM articles
		{where_clause}
		ORDER BY crawled_at DESC
		LIMIT ?
		""",
		(*params, limit),
	)

@st.cache_data(ttl=3600, show_spinner=False)
def get_latest_articles(limit: int = 500) -> pd.DataFrame:
	return cached_read_sql(
		"""
		SELECT
			article_id, title, summary, content_text, source, category,
			url, predicted_label, prediction_score,
			published_at, crawled_at
		FROM articles
		ORDER BY crawled_at DESC
		LIMIT ?
		""",
		(limit,),
	)

def get_latest_hot_topics(hours: int) -> pd.DataFrame:
	"""Get latest hot_topics snapshot for a timeframe; fallback to latest snapshot overall."""
	return uncached_read_sql(
		"""
		SELECT id, topic_name, keywords, article_count, timeframe, created_at
		FROM hot_topics
		WHERE timeframe = ?
		  AND created_at = (
			SELECT MAX(created_at)
			FROM hot_topics
			WHERE timeframe = ?
		  )
		ORDER BY article_count DESC, id ASC
		""",
		(hours, hours),
	)


def get_hot_topics_for_feed(hours: int, limit: int = HOT_TOPIC_FEED_LIMIT) -> pd.DataFrame:
	"""Return up to *limit* topics for a timeframe, backfilling from older snapshots if needed."""
	latest_df = get_latest_hot_topics(hours)
	if latest_df.empty:
		return latest_df

	if len(latest_df) >= limit:
		return latest_df.head(limit)

	latest_created_at = latest_df.iloc[0].get("created_at")
	needed = limit - len(latest_df)
	older_df = uncached_read_sql(
		"""
		SELECT id, topic_name, keywords, article_count, timeframe, created_at
		FROM hot_topics
		WHERE timeframe = ? AND created_at < ?
		ORDER BY created_at DESC, article_count DESC, id ASC
		LIMIT ?
		""",
		(hours, latest_created_at, needed),
	)

	if older_df.empty:
		return latest_df

	return pd.concat([latest_df, older_df], ignore_index=True)


@st.cache_data(ttl=300, show_spinner=False)
def get_latest_hot_topic_ids(hours: int) -> list[int]:
	"""Resolve one hot_topics snapshot and return its topic IDs."""
	topics_df = get_latest_hot_topics(hours)
	if topics_df.empty:
		return []
	return [int(v) for v in topics_df["id"].tolist()]


@st.cache_data(ttl=300, show_spinner=False)
def get_hot_topic_articles(
	hours: int,
	source: str,
	category: str,
	limit: int = 500,
) -> pd.DataFrame:
	"""Get articles linked to the latest hot_topics snapshot."""
	topic_ids = get_latest_hot_topic_ids(hours)
	if not topic_ids:
		return pd.DataFrame()

	placeholders = ",".join(["?"] * len(topic_ids))
	clauses = [f"ta.topic_id IN ({placeholders})"]
	params: list = list(topic_ids)

	if source and source != "Tất cả":
		clauses.append("a.source = ?")
		params.append(source)

	if category and category != "Tất cả":
		clauses.append("a.category = ?")
		params.append(category)

	where_clause = " AND ".join(clauses)

	query = f"""
		SELECT DISTINCT
			a.article_id, a.title, a.summary, a.content_text, a.source, a.category,
			a.url, a.content_html_raw, a.predicted_label, a.prediction_score,
			a.published_at, a.crawled_at
		FROM topic_articles ta
		JOIN articles a ON a.article_id = ta.article_id
		WHERE {where_clause}
		ORDER BY a.crawled_at DESC
		LIMIT ?
	"""
	return uncached_read_sql(query, (*params, limit))

def get_hot_topic_overview_stats(hours: int, source: str, category: str) -> dict:
	"""Get overview stats for the latest hot_topics snapshot."""
	topic_ids = get_latest_hot_topic_ids(hours)
	if not topic_ids:
		return {"total_articles": 0, "clickbait_count": 0, "non_clickbait_count": 0, "labeled_count": 0, "avg_score": None}

	placeholders = ",".join(["?"] * len(topic_ids))
	clauses = [f"ta.topic_id IN ({placeholders})"]
	params: list = list(topic_ids)

	if source and source != "Tất cả":
		clauses.append("a.source = ?")
		params.append(source)

	if category and category != "Tất cả":
		clauses.append("a.category = ?")
		params.append(category)

	where_clause = " AND ".join(clauses)

	query = f"""
		WITH hot_articles AS (
			SELECT DISTINCT a.article_id, a.predicted_label, a.prediction_score
			FROM topic_articles ta
			JOIN articles a ON a.article_id = ta.article_id
			WHERE {where_clause}
		)
		SELECT
			COUNT(*) AS total_articles,
			SUM(CASE WHEN predicted_label = 'clickbait' THEN 1 ELSE 0 END) AS clickbait_count,
			SUM(CASE WHEN predicted_label = 'non-clickbait' THEN 1 ELSE 0 END) AS non_clickbait_count,
			SUM(CASE WHEN predicted_label IS NOT NULL THEN 1 ELSE 0 END) AS labeled_count,
			AVG(prediction_score) AS avg_score
		FROM hot_articles
	"""
	df = uncached_read_sql(query, tuple(params))
	if df.empty:
		return {"total_articles": 0, "clickbait_count": 0, "non_clickbait_count": 0, "labeled_count": 0, "avg_score": None}
	stats = df.iloc[0].to_dict()
	stats["total_articles"] = int(stats.get("total_articles") or 0)
	stats["clickbait_count"] = int(stats.get("clickbait_count") or 0)
	stats["non_clickbait_count"] = int(stats.get("non_clickbait_count") or 0)
	stats["labeled_count"] = int(stats.get("labeled_count") or 0)
	avg_score = stats.get("avg_score")
	stats["avg_score"] = float(avg_score) if avg_score is not None else None
	return stats


def get_hot_topic_by_id(topic_id: int) -> dict | None:
	"""Get a single hot topic row by its ID."""
	df = uncached_read_sql(
		"""
		SELECT id, topic_name, keywords, article_count, timeframe, created_at
		FROM hot_topics
		WHERE id = ?
		LIMIT 1
		""",
		(int(topic_id),),
	)
	return df.iloc[0].to_dict() if not df.empty else None


def get_articles_by_topic_id(topic_id: int) -> pd.DataFrame:
	"""Get all articles linked to a specific hot topic."""
	return uncached_read_sql(
		"""
		SELECT DISTINCT
			a.article_id, a.title, a.summary, a.content_text, a.source, a.category,
			a.url, a.content_html_raw, a.predicted_label, a.prediction_score,
			a.published_at, a.crawled_at
		FROM topic_articles ta
		JOIN articles a ON a.article_id = ta.article_id
		WHERE ta.topic_id = ?
		ORDER BY a.crawled_at DESC
		""",
		(int(topic_id),),
	)

def get_article_by_id(article_id: str) -> dict | None:
	"""Get a specific article by ID as a dict"""
	df = uncached_read_sql(
		"""
		SELECT article_id, title, summary, content_text, source, category,
		       url, predicted_label, prediction_score, published_at, crawled_at
		FROM articles
		WHERE CAST(article_id AS TEXT) = ?
		LIMIT 1
		""",
		(str(article_id).strip(),),
	)
	return df.iloc[0].to_dict() if not df.empty else None

def get_overview_stats(hours: int, source: str, category: str, label: str) -> dict:
	where_clause, params = _build_article_where_clause(hours, source, category, label)
	query = f"""
		SELECT
			COUNT(*) AS total_articles,
			SUM(CASE WHEN predicted_label = 'clickbait' THEN 1 ELSE 0 END) AS clickbait_count,
			SUM(CASE WHEN predicted_label = 'non-clickbait' THEN 1 ELSE 0 END) AS non_clickbait_count,
			SUM(CASE WHEN predicted_label IS NOT NULL THEN 1 ELSE 0 END) AS labeled_count,
			AVG(prediction_score) AS avg_score
		FROM articles
		{where_clause}
	"""
	df = uncached_read_sql(query, params)
	if df.empty:
		return {"total_articles": 0, "clickbait_count": 0, "non_clickbait_count": 0, "labeled_count": 0, "avg_score": None}
	stats = df.iloc[0].to_dict()
	stats["total_articles"] = int(stats.get("total_articles") or 0)
	stats["clickbait_count"] = int(stats.get("clickbait_count") or 0)
	stats["non_clickbait_count"] = int(stats.get("non_clickbait_count") or 0)
	stats["labeled_count"] = int(stats.get("labeled_count") or 0)
	avg_score = stats.get("avg_score")
	stats["avg_score"] = float(avg_score) if avg_score is not None else None
	return stats

# CSS Styling
def inject_styles():
	st.markdown("""
	<style>
	html, body, .stApp {
		background-color: #ffffff !important;
		color: #111111 !important;
	}

	.stApp > header {
		background: #ffffff !important;
	}

	[data-testid="stAppViewContainer"],
	[data-testid="stHeader"],
	[data-testid="stToolbar"],
	[data-testid="stSidebar"],
	[data-testid="stSidebarContent"] {
		background-color: #ffffff !important;
		color: #111111 !important;
	}

	[data-testid="stSidebar"] {
		border-right: 1px solid #eee;
	}

	.block-container {
		background-color: #ffffff !important;
		color: #111111 !important;
		padding-top: 1rem;
	}

	[data-testid="stMarkdownContainer"] p,
	[data-testid="stMarkdownContainer"] span,
	[data-testid="stMarkdownContainer"] div {
		color: #111111;
	}

	a {
		color: #c41e3a;
	}

	* {
		font-family: 'Segoe UI', Arial, sans-serif;
	}
	
	.ai-news-header {
		background: white;
		border-bottom: 1px solid #ddd;
		padding: 14px 18px;
		margin: 0 0 20px 0;
		border-radius: 8px;
	}
	
	.header-top {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 10px;
	}
	
	.logo {
		font-size: 28px;
		font-weight: 900;
		letter-spacing: -1px;
	}
	
	.logo-accent {
		color: #c41e3a;
	}
	
	.header-right {
		display: flex;
		align-items: center;
		justify-content: flex-end;
		flex-wrap: wrap;
		gap: 15px;
		font-size: 13px;
		color: #666;
	}

	.search-icon {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 30px;
		height: 30px;
		border: 1px solid #ddd;
		border-radius: 50%;
		font-size: 14px;
		cursor: pointer;
		background: #fff;
		color: #444;
	}

	.search-icon:hover {
		border-color: #c41e3a;
		color: #c41e3a;
	}
	
	.navbar {
		display: flex;
		gap: 25px;
		padding: 10px 0;
		margin-top: 6px;
		border-bottom: 1px solid #eee;
		overflow-x: auto;
		font-size: 14px;
	}
	
	.nav-link {
		color: #333;
		text-decoration: none;
		white-space: nowrap;
		font-weight: 500;
	}
	
	.nav-link:hover {
		color: #c41e3a;
	}
	
	.main-container {
		display: grid;
		grid-template-columns: 2fr 1fr;
		gap: 30px;
		margin: 20px 0;
	}
	
	.featured-article {
		background: white;
		border-radius: 2px;
	}
	
	.featured-image {
		width: 100%;
		height: 300px;
		background: linear-gradient(135deg, #e0e0e0 0%, #f5f5f5 100%);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 60px;
		color: #aaa;
		margin-bottom: 15px;
	}
	
	.featured-meta {
		font-size: 12px;
		color: #999;
		margin-bottom: 8px;
	}
	
	.featured-title {
		font-size: 24px;
		font-weight: 800;
		line-height: 1.3;
		margin: 10px 0;
		font-family: Georgia, serif;
		color: #000;
	}
	
	.featured-summary {
		font-size: 15px;
		line-height: 1.6;
		color: #555;
		margin: 15px 0;
	}
	
	.featured-badge {
		display: inline-block;
		padding: 5px 12px;
		border-radius: 3px;
		font-size: 12px;
		font-weight: bold;
		margin-top: 10px;
	}
	
	.badge-clickbait {
		background: #fee;
		color: #c41e3a;
		border: 1px solid #fcc;
	}
	
	.badge-safe {
		background: #efe;
		color: #1a7;
		border: 1px solid #cfc;
	}
	
	.badge-unlabeled {
		background: #eee;
		color: #666;
		border: 1px solid #ddd;
	}
	
	.sidebar {
		background: white;
		border-radius: 2px;
		padding: 20px;
	}
	
	.sidebar-title {
		font-size: 15px;
		font-weight: 700;
		margin-bottom: 15px;
		padding-bottom: 10px;
		border-bottom: 2px solid #c41e3a;
		color: #000;
	}
	
	.sidebar-item {
		padding: 12px 0;
		border-bottom: 1px solid #eee;
		font-size: 14px;
	}
	
	.sidebar-item:last-child {
		border-bottom: none;
	}
	
	.sidebar-item-title {
		font-weight: 600;
		color: #000;
		line-height: 1.35;
		margin-bottom: 4px;
		font-size: 14px;
	}
	
	.sidebar-item-meta {
		font-size: 12px;
		color: #999;
	}
	
	.article-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 20px;
		margin: 30px 0;
	}
	
	.article-card {
		background: white;
		border-radius: 2px;
		overflow: hidden;
		border: 1px solid #eee;
		transition: all 0.3s ease;
	}
	
	.article-card:hover {
		box-shadow: 0 4px 12px rgba(0,0,0,0.1);
	}
	
	.article-card-image {
		width: 100%;
		height: 160px;
		background: linear-gradient(135deg, #f0f0f0 0%, #e8e8e8 100%);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 40px;
		color: #bbb;
	}
	
	.article-card-content {
		padding: 15px;
	}
	
	.article-card-title {
		font-size: 14px;
		font-weight: 700;
		line-height: 1.4;
		margin-bottom: 8px;
		color: #000;
		font-family: Georgia, serif;
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
		min-height: 40px;
	}
	
	.article-card-meta {
		font-size: 12px;
		color: #999;
		margin-bottom: 8px;
	}
	
	.article-card-summary {
		font-size: 13px;
		line-height: 1.5;
		color: #666;
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
		margin-bottom: 10px;
		min-height: 39px;
	}
	
	.article-detail {
		background: white;
		border: 1px solid #eee;
		border-radius: 2px;
		padding: 20px;
		margin-top: 10px;
	}
	
	.article-detail-meta {
		font-size: 12px;
		color: #999;
		margin-bottom: 10px;
	}
	
	.article-detail-body {
		font-size: 15px;
		line-height: 1.8;
		color: #222;
		white-space: pre-wrap;
		word-break: break-word;
		margin-top: 15px;
	}
	
	.article-detail-url {
		margin-top: 15px;
		font-size: 13px;
	}

	.hot-topic-wrap {
		background: #fff;
		border-radius: 4px;
	}

	.hot-topic-head {
		display: flex;
		justify-content: flex-start;
		align-items: center;
		margin: 8px 0 14px 0;
	}

	.hot-topic-title {
		font-size: 24px;
		font-family: Georgia, serif;
		font-weight: 700;
		line-height: 1.15;
		color: #141414;
	}

	.hot-topic-divider {
		border: none;
		border-top: 1px solid #ddd;
		margin: 12px 0 14px 0;
	}

	.hot-topic-item-title {
		font-size: 18px;
		line-height: 1.2;
		font-family: Georgia, serif;
		font-weight: 700;
		color: #121212;
		margin: 0 0 6px 0;
	}

	.hot-topic-item-summary {
		font-size: 14px;
		line-height: 1.5;
		color: #2e2e2e;
		margin: 0;
	}
	
	.section-title {
		font-size: 16px;
		font-weight: 700;
		margin: 40px 0 20px 0;
		padding-bottom: 10px;
		border-bottom: 2px solid #c41e3a;
		color: #000;
	}
	
	.stMetric {
		background: white !important;
		padding: 15px !important;
		border-radius: 2px !important;
		border: 1px solid #eee !important;
	}
	
	@media (max-width: 1024px) {
		.main-container {
			grid-template-columns: 1fr;
		}
		.article-grid {
			grid-template-columns: repeat(2, 1fr);
		}
		.hot-topic-title,
		.hot-topic-item-title {
			font-size: 20px;
		}
		.hot-topic-item-summary {
			font-size: 13px;
		}
	}
	
	@media (max-width: 768px) {
		.article-grid {
			grid-template-columns: 1fr;
		}
		.hot-topic-title,
		.hot-topic-item-title {
			font-size: 18px;
		}
		.hot-topic-item-summary {
			font-size: 13px;
		}
	}
	</style>
	""", unsafe_allow_html=True)

def render_header():
	"""Render AI News header"""
	now = datetime.now()
	weekday_map = {
		0: "Thứ Hai",
		1: "Thứ Ba",
		2: "Thứ Tư",
		3: "Thứ Năm",
		4: "Thứ Sáu",
		5: "Thứ Bảy",
		6: "Chủ Nhật",
	}
	date_label = f"{weekday_map[now.weekday()]}, {now.strftime('%d/%m/%Y')}"
	topic_mode = st.session_state.get("header_topic_mode", "Tất cả")
	st.markdown("<div class='ai-news-header'>", unsafe_allow_html=True)
	col_left, col_right = st.columns([3, 2])
	with col_left:
		st.markdown("<div class='logo'>VnNew<span class='logo-accent'>AI</span></div>", unsafe_allow_html=True)
	with col_right:
		right_col1, right_col2, right_col3 = st.columns([4, 4, 1])
		with right_col1:
			st.markdown(f"<div class='header-right'><span>{date_label}</span></div>", unsafe_allow_html=True)
		with right_col2:
			topic_mode = st.radio(
				"Chế độ bài viết",
				options=["Tất cả", "Chủ đề nóng"],
				horizontal=True,
				label_visibility="collapsed",
				key="header_topic_mode",
			)
		with right_col3:
			if st.button("🔍", key="open_search_page", help="Mở trang tìm kiếm"):
				st.session_state.current_view = "search"
				st.rerun()
	st.markdown("</div>", unsafe_allow_html=True)
	return topic_mode

def render_search_page():
	"""Render search page opened from header icon."""
	st.markdown("## Tìm kiếm")

	if st.button("← Quay lại trang chính", key="back_from_search"):
		st.session_state.current_view = "home"
		st.rerun()

	search_text = st.text_input("", placeholder="Tìm kiếm", key="search_query")

	col1, col2 = st.columns(2)
	with col1:
		time_filter = st.selectbox(
			"Thời gian",
			options=["Tất cả"] + list(TIMEFRAME_OPTIONS.keys()),
			index=0,
			key="search_time_filter",
		)
	with col2:
		categories = get_distinct_values("category")
		category_filter = st.selectbox(
			"Chuyên mục",
			options=["Tất cả"] + categories,
			index=0,
			format_func=normalize_category_label,
			key="search_category_filter",
		)

	st.divider()

# Get hours from timeframe filter (0 means all)
	if time_filter == "Tất cả":
		hours = 0
	else:
		hours = TIMEFRAME_OPTIONS.get(time_filter, 0)
	category = category_filter if category_filter != "Tất cả" else "Tất cả"
	articles_df = get_recent_articles(hours, "Tất cả", category, "Tất cả", limit=300)

	if search_text.strip():
		query = search_text.strip().lower()
		mask = (
			articles_df["title"].fillna("").str.lower().str.contains(query)
			| articles_df["summary"].fillna("").str.lower().str.contains(query)
		)
		articles_df = articles_df[mask]

	if articles_df.empty:
		st.info("Không tìm thấy bài viết phù hợp.")
		return

	st.markdown(f"Tìm thấy **{len(articles_df):,}** bài viết")
	for article in articles_df.head(30).to_dict("records"):
		title = str(article.get("title", ""))
		summary = str(article.get("summary", ""))
		source = str(article.get("source", ""))
		category_name = normalize_category_label(article.get("category", ""))
		article_id = article.get("article_id")

		st.markdown(
			f"""
			<div style="border:1px solid #eee; border-radius:8px; padding:12px; margin-bottom:10px; background:#fff;">
				<div style="font-weight:700; margin-bottom:6px;">{html.escape(title)}</div>
				<div style="font-size:12px; color:#666; margin-bottom:6px;">{html.escape(source)} · {html.escape(category_name)}</div>
				<div style="font-size:13px; color:#444;">{html.escape(summary[:180])}</div>
			</div>
			""",
			unsafe_allow_html=True,
		)
		if st.button("🔍 Đọc bài", key=f"search_read_{article_id}"):
			st.session_state.selected_article_id = str(article_id)
			st.session_state.current_view = "home"
			st.rerun()

def render_category_nav(categories: list[str]):
	"""Render category chips based on available article categories."""
	# Filter important categories only
	important_categories = {"kinh-te", "xa-hoi"}
	filtered = [cat for cat in categories if cat in important_categories]
	
	if not filtered:
		return
	st.markdown("<div class='sidebar-title' style='margin-top: 10px;'>DANH MỤC BÁO</div>", unsafe_allow_html=True)
	chips = " ".join(
		f"<span style='display:inline-block;padding:6px 10px;margin:0 8px 8px 0;border:1px solid #eee;border-radius:999px;background:#fafafa;font-size:13px;'>{html.escape(normalize_category_label(cat))}</span>"
		for cat in filtered[:8]
	)
	st.markdown(f"<div style='margin-bottom: 10px;'>{chips}</div>", unsafe_allow_html=True)

def get_badge_html(label, score):
	"""Get badge HTML based on label"""
	if label == "clickbait":
		badge_class = "badge-clickbait"
		text = "⚠️ Clickbait"
	elif label == "non-clickbait":
		badge_class = "badge-safe"
		text = "✓ Xác thực"
	else:
		badge_class = "badge-unlabeled"
		text = "? Chưa gán"
	return f'<span class="featured-badge {badge_class}">{text}</span>'

def render_featured_article(article):
	"""Render featured article"""
	article_id = article.get("article_id")
	title = html.escape(str(article.get("title", ""))[:100])
	summary = html.escape(str(article.get("summary", ""))[:200])
	source = html.escape(str(article.get("source", "")))
	category = html.escape(normalize_category_label(article.get("category", "")))
	badge = get_badge_html(article.get("predicted_label"), article.get("prediction_score"))
	
	st.markdown(f"""
	<div class="featured-article">
		<div style="padding: 15px;">
			<div class="featured-meta"><b>{source}</b> · {category}</div>
			<h1 class="featured-title">{title}</h1>
			<p class="featured-summary">{summary}</p>
			{badge}
		</div>
	</div>
	""", unsafe_allow_html=True)
	
	if st.button("🔍 Xem chi tiết", key=f"featured_btn_{article_id}"):
		st.session_state.selected_article_id = article_id
		st.rerun()

def render_article_detail(article):
	"""Render full article content for reading."""
	title = html.escape(str(article.get("title", "")))
	summary = html.escape(str(article.get("summary", "")))
	content_text = str(article.get("content_text", "") or "").strip()
	content_html = html.escape(content_text).replace("\n", "<br>") if content_text else html.escape("Không có nội dung đầy đủ. Vui lòng xem tóm tắt bên trên hoặc mở bài gốc.")
	source = html.escape(str(article.get("source", "")))
	category = html.escape(normalize_category_label(article.get("category", "")))
	published_at = html.escape(str(article.get("published_at") or ""))
	crawled_at = html.escape(str(article.get("crawled_at") or ""))
	badge = get_badge_html(article.get("predicted_label"), article.get("prediction_score"))
	url = str(article.get("url", "") or "").strip()
	url_html = f'<div class="article-detail-url">🔗 <a href="{html.escape(url)}" target="_blank" rel="noopener noreferrer">Mở bài gốc</a></div>' if url else ""

	st.markdown(
		f"""
		<div class="article-detail">
			<div class="article-detail-meta"><b>{source}</b> · {category} · {published_at or crawled_at}</div>
			<h2 style="margin: 0 0 10px 0; font-family: Georgia, serif;">{title}</h2>
			<div style="margin-bottom: 10px;">{badge}</div>
			<p style="font-size: 16px; line-height: 1.7; color: #444; margin: 0;">{summary}</p>
			<div class="article-detail-body">{content_html}</div>
			{url_html}
		</div>
		""",
		unsafe_allow_html=True,
	)

def render_sidebar_highlights(articles):
	"""Render sidebar highlights"""
	st.markdown("""
	<div class="sidebar">
		<div class="sidebar-title">TIN NỔI BẬT</div>
	""", unsafe_allow_html=True)
	
	for idx, article in enumerate(articles[:4]):
		title = html.escape(str(article.get("title", ""))[:80])
		source = html.escape(str(article.get("source", "")))
		article_id = article.get("article_id")
		
		st.markdown(f"""
		<div class="sidebar-item">
			<div class="sidebar-item-title">{title}</div>
			<div class="sidebar-item-meta">{source}</div>
		</div>
		""", unsafe_allow_html=True)

		if article_id is not None:
			if st.button("🔍 Đọc bài", key=f"highlight_read_{article_id}_{idx}", use_container_width=True):
				st.session_state.selected_article_id = str(article_id)
				st.rerun()
	
	st.markdown("</div>", unsafe_allow_html=True)


def render_hot_topic_feed(topics: list[dict]):
	"""Render hot-topic list using topic content from hot_topics table."""
	st.markdown('<div class="hot-topic-wrap">', unsafe_allow_html=True)
	header_col_left, header_col_right = st.columns([2.2, 1.8], gap="large")
	with header_col_left:
		st.markdown('<div class="hot-topic-title">Chủ đề hot trên cộng đồng</div>', unsafe_allow_html=True)
	with header_col_right:
		st.selectbox(
			"",
			options=list(HOT_TOPIC_TIMEFRAME_OPTIONS.keys()),
			index=2,
			key="hot_topic_timeframe",
			label_visibility="collapsed",
		)

	st.markdown('<hr class="hot-topic-divider" />', unsafe_allow_html=True)
	st.markdown('</div>', unsafe_allow_html=True)

	for idx, topic in enumerate(topics[:HOT_TOPIC_FEED_LIMIT]):
		topic_id = topic.get("id")
		title = html.escape(str(topic.get("topic_name", "") or "(Không có topic_name)"))
		article_count = int(topic.get("article_count") or 0)
		summary = f"{article_count:,} bài báo"

		st.markdown(
			f'''
			<div style="padding: 6px 0 4px 0;">
				<h3 class="hot-topic-item-title">{title}</h3>
				<p class="hot-topic-item-summary">{summary}</p>
			</div>
			''',
			unsafe_allow_html=True,
		)
		if st.button("Xem chủ đề", key=f"hot_topic_open_{topic_id}_{idx}"):
			st.session_state.selected_article_id = None
			st.session_state.selected_topic_id = int(topic_id)
			st.session_state.current_view = "topic_detail"
			st.rerun()

		if idx < min(len(topics), HOT_TOPIC_FEED_LIMIT) - 1:
			st.markdown('<hr class="hot-topic-divider" />', unsafe_allow_html=True)


def render_topic_detail(topic_id: int):
	"""Render a dedicated page for a hot topic and its linked articles."""
	topic = get_hot_topic_by_id(topic_id)
	if not topic:
		st.error("Không tìm thấy topic")
		if st.button("← Quay lại"):
			st.session_state.selected_topic_id = None
			st.session_state.current_view = "home"
			st.rerun()
		return

	articles_df = get_articles_by_topic_id(topic_id)

	col1, col2 = st.columns([1, 10])
	with col1:
		if st.button("← Quay lại"):
			st.session_state.selected_topic_id = None
			st.session_state.current_view = "home"
			st.rerun()

	st.markdown(
		f"""
		<div class="article-detail">
			<div class="article-detail-meta"><b>Hot topic</b> · {html.escape(str(topic.get('timeframe') or ''))}h · {html.escape(str(topic.get('created_at') or ''))}</div>
			<h2 style="margin: 0 0 10px 0; font-family: Georgia, serif;">{html.escape(str(topic.get('topic_name') or ''))}</h2>
		</div>
		""",
		unsafe_allow_html=True,
	)

	if articles_df.empty:
		st.info("Chủ đề này chưa có bài viết liên kết.")
		return

	st.markdown(f"### Bài viết trong chủ đề ({len(articles_df):,})")
	for idx, article in enumerate(articles_df.to_dict("records")):
		title = html.escape(str(article.get("title", "") or "(Không có tiêu đề)"))
		summary = html.escape(str(article.get("summary", "") or "Chưa có tóm tắt."))
		source = html.escape(str(article.get("source", "")))
		published_at = html.escape(str(article.get("published_at") or article.get("crawled_at") or ""))

		st.markdown(
			f"""
			<div style="border: 1px solid #eee; border-radius: 6px; padding: 12px; margin-bottom: 10px; background: white;">
				<div style="font-size: 12px; color: #777; margin-bottom: 6px;">{source} · {published_at}</div>
				<div style="font-size: 18px; font-weight: 700; font-family: Georgia, serif; margin-bottom: 6px;">{title}</div>
				<div style="font-size: 14px; color: #444; line-height: 1.5;">{summary}</div>
			</div>
			""",
			unsafe_allow_html=True,
		)
		if st.button("🔍 Đọc bài", key=f"topic_detail_read_{topic_id}_{idx}"):
			st.session_state.selected_article_id = str(article.get("article_id"))
			st.rerun()


def render_article_detail(article_id):
	"""Render detail page for a specific article"""
	article = get_article_by_id(article_id)
	
	if not article:
		st.error("Không tìm thấy bài báo")
		if st.button("← Quay lại"):
			st.session_state.selected_article_id = None
			st.rerun()
		return
	
	# Header with back button
	col1, col2 = st.columns([1, 10])
	with col1:
		if st.button("← Quay lại"):
			st.session_state.selected_article_id = None
			st.rerun()
	
	# Article content
	title = article.get("title", "")
	source = html.escape(str(article.get("source", "")))
	category = normalize_category_label(article.get("category", ""))
	published_at = article.get("published_at", "")
	crawled_at = article.get("crawled_at", "")
	content_text = article.get("content_text", "")
	summary = article.get("summary", "")
	url = article.get("url", "")
	label = article.get("predicted_label", "Chưa gán nhãn")
	score = article.get("prediction_score", 0)
	
	st.markdown(f"""
	<style>
		.article-detail-page {{
			padding: 20px;
			background: white;
			border-radius: 8px;
		}}
		.article-detail-title {{
			font-size: 28px;
			font-weight: bold;
			margin-bottom: 15px;
			color: #1a1a1a;
		}}
		.article-detail-meta {{
			display: flex;
			gap: 20px;
			margin-bottom: 15px;
			font-size: 14px;
			color: #666;
		}}
		.article-detail-meta-item {{
			display: flex;
			align-items: center;
			gap: 5px;
		}}
		.article-detail-badge {{
			display: inline-block;
			padding: 8px 12px;
			border-radius: 20px;
			font-size: 13px;
			font-weight: bold;
			margin-bottom: 20px;
		}}
		.badge-clickbait {{
			background: #ffe0e0;
			color: #cc0000;
		}}
		.badge-non-clickbait {{
			background: #e0f0ff;
			color: #0066cc;
		}}
		.article-detail-content {{
			font-size: 16px;
			line-height: 1.8;
			color: #333;
			margin: 20px 0;
		}}
	</style>
	<div class="article-detail-page">
		<div class="article-detail-title">{html.escape(title)}</div>
		<div class="article-detail-meta">
			<div class="article-detail-meta-item"><strong>Nguồn:</strong> {source}</div>
			<div class="article-detail-meta-item"><strong>Danh mục:</strong> {category}</div>
			<div class="article-detail-meta-item"><strong>Xuất bản:</strong> {published_at}</div>
		</div>
	</div>
	""", unsafe_allow_html=True)
	
	# Badge
	if label == "clickbait":
		badge_html = f'<div class="article-detail-badge badge-clickbait">🚨 Clickbait ({score:.2%})</div>'
	elif label == "non-clickbait":
		badge_html = f'<div class="article-detail-badge badge-non-clickbait">✅ Bình thường ({score:.2%})</div>'
	else:
		badge_html = '<div class="article-detail-badge">⏳ Chưa gán nhãn</div>'
	
	st.markdown(badge_html, unsafe_allow_html=True)
	
	# Summary
	if summary:
		st.markdown("### 📌 Tóm tắt")
		st.write(summary)
	
	# Content
	if content_text:
		st.markdown("### 📄 Nội dung")
		st.write(content_text)
	
	# URL
	if url:
		st.markdown("### 🔗 Liên kết")
		st.markdown(f"[Đọc trên trang gốc]({url})", unsafe_allow_html=False)
	
	# Metadata
	st.divider()
	col1, col2, col3 = st.columns(3)
	with col1:
		st.metric("ID", article_id)
	with col2:
		st.metric("Đã gán nhãn", label)
	with col3:
		st.metric("Độ tin cậy", f"{score:.2%}" if score else "N/A")

def render_article_grid(articles):
	"""Render article grid"""
	st.markdown("<div class='article-grid'>", unsafe_allow_html=True)
	
	for article in articles:
		article_id = article.get("article_id")
		title = html.escape(str(article.get("title", ""))[:70])
		summary = html.escape(str(article.get("summary", ""))[:80])
		source = html.escape(str(article.get("source", "")))
		category = html.escape(normalize_category_label(article.get("category", "")))
		badge = get_badge_html(article.get("predicted_label"), article.get("prediction_score"))
		
		st.markdown(f"""
		<div class="article-card" onclick="window.location.href='?article_id={article_id}'" style="cursor: pointer;">
			<div class="article-card-content">
				<div class="article-card-title">{title}</div>
				<div class="article-card-meta">{source} · {category}</div>
				<div class="article-card-summary">{summary}</div>
				<div style="font-size: 12px; font-weight: bold;">{badge}</div>
			</div>
		</div>
		""", unsafe_allow_html=True)

def render_article_grid_clickable(articles):
	"""Render article grid with clickable cards"""
	cols = st.columns(2)
	for idx, article in enumerate(articles):
		article_id = article.get("article_id")
		title = str(article.get("title", ""))[:70]
		summary = str(article.get("summary", ""))[:100]
		source = str(article.get("source", ""))
		category = normalize_category_label(article.get("category", ""))
		label = article.get("predicted_label", "unknown")
		score = article.get("prediction_score", 0)
		
		with cols[idx % 2]:
			# Create a container for the card
			st.markdown(f"""
			<div style="border: 1px solid #ddd; border-radius: 8px; padding: 12px; margin-bottom: 12px; background: white;">
				<div style="font-weight: bold; margin-bottom: 8px; color: #1a1a1a;">{html.escape(title)}</div>
				<div style="font-size: 12px; color: #666; margin-bottom: 8px;">{html.escape(source)} · {html.escape(category)}</div>
				<div style="font-size: 13px; color: #444; margin-bottom: 10px; line-height: 1.4;">{html.escape(summary)}</div>
				<div style="font-size: 11px; color: #666;">
					{'🚨 Clickbait' if label == 'clickbait' else '✅ Bình thường' if label == 'non-clickbait' else '⏳ Chưa gán'} ({score:.0%})
				</div>
			</div>
			""", unsafe_allow_html=True)
			
			if st.button("🔍 Xem chi tiết", key=f"article_btn_{article_id}"):
				st.session_state.selected_article_id = article_id
				st.rerun()
	
	
	st.markdown("</div>", unsafe_allow_html=True)

def main():
	ensure_database()
	inject_styles()
	
	# Initialize session state
	if "selected_article_id" not in st.session_state:
		st.session_state.selected_article_id = None
	if "selected_topic_id" not in st.session_state:
		st.session_state.selected_topic_id = None
	if "current_view" not in st.session_state:
		st.session_state.current_view = "home"
	
	# Check if article detail view should be shown
	if st.session_state.selected_article_id:
		render_article_detail(st.session_state.selected_article_id)
		return

	if st.session_state.current_view == "topic_detail" and st.session_state.selected_topic_id is not None:
		render_topic_detail(st.session_state.selected_topic_id)
		return

	if st.session_state.current_view == "search":
		render_search_page()
		return
	
	categories = get_distinct_values("category")
	
	# Default filter values (sidebar disabled)
	hours_val = 24  # Default for normal mode
	source = "Tất cả"
	category_options = ["Tất cả"] + categories
	category = "Tất cả"
	label = "Tất cả"
	
	# Initialize session state for hot topic timeframe if not exists
	if "hot_topic_timeframe" not in st.session_state:
		st.session_state.hot_topic_timeframe = "24 giờ"
	
	# Main content
	topic_mode = render_header()
	if topic_mode == "Chủ đề nóng":
		hot_timeframe = st.session_state.get("hot_topic_timeframe", "24 giờ")
		hours_val = HOT_TOPIC_TIMEFRAME_OPTIONS.get(hot_timeframe, 24)
	if topic_mode != "Chủ đề nóng":
		render_category_nav(categories)
		selected_category = st.selectbox(
			"Thể loại báo",
			options=category_options,
			index=0,
			format_func=normalize_category_label,
			key="selected_category",
		)
		category = selected_category
	else:
		category = "Tất cả"
	
	# Get articles
	if topic_mode == "Chủ đề nóng":
		hot_topics_df = get_latest_hot_topics(hours_val)
		hot_topics_feed_df = get_hot_topics_for_feed(hours_val, HOT_TOPIC_FEED_LIMIT)
		articles = get_hot_topic_articles(hours_val, source, category)
		if articles.empty and hot_topics_df.empty:
			st.info("🔥 Chưa có dữ liệu chủ đề nóng trong bảng hot_topics cho bộ lọc hiện tại.")
			return
		stats = get_hot_topic_overview_stats(hours_val, source, category)
		db_total_articles = get_sqlite_sequence_value("articles")
		db_hot_topics = get_sqlite_sequence_value("hot_topics")
	else:
		hot_topics_df = pd.DataFrame()
		hot_topics_feed_df = pd.DataFrame()
		articles = get_recent_articles(hours_val, source, category, label)
		if articles.empty:
			articles = get_latest_articles()
			if articles.empty:
				st.info("📰 Chưa có bài viết nào trong cơ sở dữ liệu.")
				return
		stats = get_overview_stats(hours_val, source, category, label)
		db_total_articles = get_sqlite_sequence_value("articles")
		db_hot_topics = get_sqlite_sequence_value("hot_topics")
	
	# Stats
	if topic_mode == "Chủ đề nóng":
		col1, col2, col3, col4, col5 = st.columns(5)
	else:
		col1, col2, col3, col4 = st.columns(4)
	with col1:
		st.metric("Tổng bài", f"{db_total_articles:,}")
	if topic_mode == "Chủ đề nóng":
		with col2:
			st.metric("Hot topics", f"{db_hot_topics:,}")
		with col3:
			labeled = stats['labeled_count'] or 0
			st.metric("Đã gán nhãn", f"{labeled:,}")
		with col4:
			clickbait = stats['clickbait_count'] or 0
			st.metric("Clickbait", f"{clickbait:,}")
		with col5:
			labeled = stats['labeled_count'] or 0
			clickbait = stats['clickbait_count'] or 0
			if labeled > 0:
				ratio = (clickbait / labeled * 100)
				st.metric("Tỷ lệ", f"{ratio:.1f}%")
			else:
				st.metric("Tỷ lệ", "0%")
	else:
		with col2:
			labeled = stats['labeled_count'] or 0
			st.metric("Đã gán nhãn", f"{labeled:,}")
		with col3:
			clickbait = stats['clickbait_count'] or 0
			st.metric("Clickbait", f"{clickbait:,}")
		with col4:
			labeled = stats['labeled_count'] or 0
			clickbait = stats['clickbait_count'] or 0
			if labeled > 0:
				ratio = (clickbait / labeled * 100)
				st.metric("Tỷ lệ", f"{ratio:.1f}%")
			else:
				st.metric("Tỷ lệ", "0%")
	
	# Featured + Sidebar layout
	if topic_mode == "Chủ đề nóng":
		render_hot_topic_feed(hot_topics_feed_df.to_dict("records"))
		if articles.empty:
			st.info("Snapshot hot_topics có topic, nhưng chưa có bài viết liên kết trong topic_articles.")
		return

	col_left, col_right = st.columns([2, 1], gap="large")
	
	with col_left:
		render_featured_article(articles.iloc[0].to_dict())
	
	with col_right:
		render_sidebar_highlights(articles.iloc[1:].to_dict("records"))

	# Article grid - clickable cards
	st.markdown("<h3 class='section-title'>TIN MỚI NHẤT (Bấm để xem chi tiết)</h3>", unsafe_allow_html=True)
	
	grid_articles = articles.iloc[5:].to_dict("records")
	if grid_articles:
		render_article_grid_clickable(grid_articles)

if __name__ == "__main__":
	main()

