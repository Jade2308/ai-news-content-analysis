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

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DB_PATH
from src.database.schema import init_db
from src.streamlit.dashboard_ui import (
	premium_dashboard_styles,
	render_article_card_html,
	render_dashboard_hero,
	render_topic_card_html,
)

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


def prepare_article_records(df: pd.DataFrame) -> list[dict]:
	"""Sanitize article DataFrame and return list of dict records.

	Ensures `prediction_score` exists and is a float within [0.0, 1.0].
	Returns an empty list for empty/None inputs.
	"""
	if df is None or df.empty:
		return []
	df = df.copy()
	if "prediction_score" in df.columns:
		df["prediction_score"] = pd.to_numeric(df["prediction_score"], errors="coerce").fillna(0.0).clip(0.0, 1.0)
	else:
		df["prediction_score"] = 0.0
	# Convert to native python types for safety
	return df.to_dict("records")

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
	st.markdown(premium_dashboard_styles(), unsafe_allow_html=True)

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
	st.markdown("<div class='dashboard-shell'>", unsafe_allow_html=True)
	st.markdown(render_dashboard_hero(date_label, topic_mode, 0, 0), unsafe_allow_html=True)
	control_col1, control_col2, control_col3 = st.columns([1.3, 1.3, 1])
	with control_col1:
		topic_mode = st.radio(
			"Chế độ bài viết",
			options=["Tất cả", "Chủ đề nóng"],
			horizontal=True,
			label_visibility="collapsed",
			key="header_topic_mode",
		)
	with control_col2:
		st.markdown(f"<div class='filter-panel'><div class='metric-label'>Ngày hiện tại</div><div class='metric-value' style='font-size: 22px;'>{html.escape(date_label)}</div><div class='metric-help'>Giao diện newsroom premium được tối ưu cho đọc nhanh và drill-down.</div></div>", unsafe_allow_html=True)
	with control_col3:
		if st.button("🔍 Mở tìm kiếm", key="open_search_page", use_container_width=True, help="Mở trang tìm kiếm"):
			st.session_state.current_view = "search"
			st.rerun()
	return topic_mode

def render_search_page():
	"""Render search page opened from header icon."""
	st.markdown("<div class='dashboard-shell'><div class='search-shell'>", unsafe_allow_html=True)
	st.markdown("<div class='search-title'>Search</div>", unsafe_allow_html=True)
	st.markdown("<h2 class='dashboard-title' style='font-size: clamp(26px, 3vw, 38px); margin-bottom: 8px;'>Tìm kiếm bài viết</h2>", unsafe_allow_html=True)
	st.markdown("<div class='dashboard-subtitle'>Khám phá bài viết theo từ khóa, thời gian và chuyên mục với giao diện ưu tiên tốc độ đọc và drill-down.</div>", unsafe_allow_html=True)

	if st.button("← Quay lại trang chính", key="back_from_search"):
		st.session_state.current_view = "home"
		st.rerun()

	search_text = st.text_input("Tìm kiếm", placeholder="Tìm kiếm", key="search_query", label_visibility="collapsed")

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
		st.markdown("</div></div>", unsafe_allow_html=True)
		return

	st.markdown(f"Tìm thấy **{len(articles_df):,}** bài viết")
	for article in prepare_article_records(articles_df.head(30)):
		title = str(article.get("title", ""))
		summary = str(article.get("summary", ""))
		source = str(article.get("source", ""))
		category_name = normalize_category_label(article.get("category", ""))
		article_id = article.get("article_id")
		badge = get_badge_html(article.get("predicted_label"), article.get("prediction_score"))

		st.markdown(
			render_article_card_html(title, summary[:180], source, category_name, badge, article_id),
			unsafe_allow_html=True,
		)
		if st.button("🔍 Đọc bài", key=f"search_read_{article_id}"):
			st.session_state.selected_article_id = str(article_id)
			st.session_state.current_view = "home"
			st.rerun()
	st.markdown("</div></div>", unsafe_allow_html=True)

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
	<div class="article-featured">
		<div class="detail-meta"><b>{source}</b> · {category}</div>
		<h1 class="dashboard-title" style="font-size: clamp(24px, 2.8vw, 36px); margin: 8px 0 12px;">{title}</h1>
		<p class="dashboard-subtitle" style="margin: 0 0 14px; max-width: 100%;">{summary}</p>
		{badge}
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
	st.markdown('<div class="topic-shell"><div class="hot-topic-wrap">', unsafe_allow_html=True)
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
	st.markdown('</div></div>', unsafe_allow_html=True)

	for idx, topic in enumerate(topics[:HOT_TOPIC_FEED_LIMIT]):
		topic_id = topic.get("id")
		title = html.escape(str(topic.get("topic_name", "") or "(Không có topic_name)"))
		article_count = int(topic.get("article_count") or 0)
		summary = f"{article_count:,} bài báo"

		st.markdown(
			render_topic_card_html(title, summary, f"Snapshot {article_count:,} bài"),
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
		<div class="topic-shell">
			<div class="article-detail">
				<div class="article-detail-meta"><b>Hot topic</b> · {html.escape(str(topic.get('timeframe') or ''))}h · {html.escape(str(topic.get('created_at') or ''))}</div>
				<h2 style="margin: 0 0 10px 0; font-size: clamp(26px, 3vw, 40px);">{html.escape(str(topic.get('topic_name') or ''))}</h2>
			</div>
		</div>
		""",
		unsafe_allow_html=True,
	)

	if articles_df.empty:
		st.info("Chủ đề này chưa có bài viết liên kết.")
		return

	st.markdown(f"### Bài viết trong chủ đề ({len(articles_df):,})")
	for idx, article in enumerate(prepare_article_records(articles_df)):
		title = html.escape(str(article.get("title", "") or "(Không có tiêu đề)"))
		summary = html.escape(str(article.get("summary", "") or "Chưa có tóm tắt."))
		source = html.escape(str(article.get("source", "")))
		published_at = html.escape(str(article.get("published_at") or article.get("crawled_at") or ""))

		st.markdown(
			f"""
			<div class="detail-card">
				<div class="detail-meta">{source} · {published_at}</div>
				<div class="topic-card-title" style="font-size: 18px;">{title}</div>
				<div class="topic-card-summary">{summary}</div>
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

	col1, _ = st.columns([1, 10])
	with col1:
		if st.button("← Quay lại"):
			st.session_state.selected_article_id = None
			st.rerun()

	title = html.escape(str(article.get("title", "")))
	source = html.escape(str(article.get("source", "")))
	category = html.escape(normalize_category_label(article.get("category", "")))
	published_at = html.escape(str(article.get("published_at", "")))
	crawled_at = html.escape(str(article.get("crawled_at", "")))
	content_text = str(article.get("content_text", "") or "").strip()
	summary = html.escape(str(article.get("summary", "") or ""))
	url = str(article.get("url", "") or "").strip()
	label = article.get("predicted_label", "Chưa gán nhãn")
	raw_score = article.get("prediction_score", 0)
	try:
		score = float(raw_score) if raw_score is not None else 0.0
	except (TypeError, ValueError):
		score = 0.0

	badge_html = get_badge_html(label, score)
	content_html = html.escape(content_text).replace("\n", "<br>") if content_text else "Chưa có nội dung đầy đủ."
	url_html = f'<div class="article-detail-url">🔗 <a href="{html.escape(url)}" target="_blank" rel="noopener noreferrer">Mở bài gốc</a></div>' if url else ""

	st.markdown(
		f"""
		<div class="detail-shell">
			<div class="article-detail">
				<div class="article-detail-meta"><b>{source}</b> · {category} · {published_at or crawled_at}</div>
				<h2 style="margin: 0 0 10px 0; font-size: clamp(26px, 3vw, 40px); line-height: 1.15;">{title}</h2>
				<div style="margin-bottom: 10px;">{badge_html}</div>
				<p style="font-size: 16px; line-height: 1.7; color: var(--muted-strong); margin: 0;">{summary}</p>
				<div class="article-detail-body">{content_html}</div>
				{url_html}
			</div>
		</div>
		""",
		unsafe_allow_html=True,
	)

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
		raw_score = article.get("prediction_score", 0)
		try:
			score = float(raw_score) if raw_score is not None else 0.0
		except (TypeError, ValueError):
			score = 0.0
		
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
		featured = prepare_article_records(articles.head(1))
		if featured:
			render_featured_article(featured[0])
	
	with col_right:
		render_sidebar_highlights(prepare_article_records(articles.iloc[1:]))

	# Article grid - clickable cards
	st.markdown("<h3 class='section-title'>TIN MỚI NHẤT</h3>", unsafe_allow_html=True)
	st.markdown("<div class='section-subtitle'>Bấm vào từng thẻ để xem chi tiết bài viết trong bố cục premium mới.</div>", unsafe_allow_html=True)
	
	grid_articles = prepare_article_records(articles.iloc[5:])
	if grid_articles:
		render_article_grid_clickable(grid_articles)

	st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
	main()

