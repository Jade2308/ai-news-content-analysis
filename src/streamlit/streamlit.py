"""
AI News Dashboard
English Streamlit interface for AI-powered news analysis.
"""

from __future__ import annotations

import html
import sqlite3
import sys
from pathlib import Path
from typing import Sequence

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DB_PATH
from src.database.schema import init_db
from src.streamlit.theme import (
	premium_dashboard_styles,
	render_article_card_html,
)

def get_query_param(key: str) -> str | None:
	if hasattr(st, "query_params"):
		return st.query_params.get(key)
	else:
		params = st.experimental_get_query_params()
		return params.get(key, [None])[0]

def clear_query_params():
	if hasattr(st, "query_params"):
		st.query_params.clear()
	else:
		st.experimental_set_query_params()

# Page config
st.set_page_config(
	page_title="AI News Analysis - Dashboard",
	page_icon="📰",
	layout="wide",
	initial_sidebar_state="expanded"
)

TIMEFRAME_OPTIONS = {
	"1 hour": 1,
	"6 hours": 6,
	"12 hours": 12,
	"24 hours": 24,
	"7 days": 168,
}

HOT_TOPIC_TIMEFRAME_OPTIONS = {
	"1 hour": 1,
	"6 hours": 6,
	"24 hours": 24,
	"1 week": 168,
}

ALL_OPTION = "All"
UNLABELED_OPTION = "Unlabeled"
LATEST_OPTION = "Latest"

LABEL_OPTIONS = [
	ALL_OPTION,
	"clickbait",
	"non-clickbait",
	UNLABELED_OPTION,
]

NAV_OVERVIEW = "📊 Overview"
NAV_ARTICLES = "📰 Article Explorer"
NAV_TOPICS = "🔥 Hot Topics"

CATEGORY_LABELS_EN = {
	"thoi-su": "Current Affairs & Politics",
	"the-gioi": "World",
	"kinh-doanh-bds": "Business & Real Estate",
	"phap-luat": "Law",
	"khoa-hoc-cong-nghe": "Science & Technology",
	"the-thao": "Sports",
	"giai-tri-van-hoa": "Entertainment & Culture",
	"giao-duc": "Education",
	"suc-khoe": "Health",
	"doi-song-ban-doc": "Lifestyle & Readers",
	"du-lich": "Travel",
	"xe": "Automotive",
	"khac": "Other",
}

# Database functions
@st.cache_resource(show_spinner=False)
def ensure_database() -> None:
	init_db(DB_PATH, verbose=False)

@st.cache_data(ttl=300, show_spinner=False)
def cached_read_sql(query: str, params: Sequence | None = None) -> pd.DataFrame:
	with sqlite3.connect(DB_PATH) as conn:
		return pd.read_sql_query(query, conn, params=params or ())

def uncached_read_sql(query: str, params: Sequence | None = None) -> pd.DataFrame:
	"""Read SQL without caching - for dynamic queries like stats"""
	with sqlite3.connect(DB_PATH) as conn:
		return pd.read_sql_query(query, conn, params=params or ())

@st.cache_data(ttl=300, show_spinner=False)
def get_row_count(table_name: str) -> int:
	"""Return the actual count of rows in a table."""
	if table_name not in ["articles", "hot_topics", "topic_articles"]:
		return 0
	df = uncached_read_sql(f"SELECT COUNT(*) AS count FROM {table_name}")
	if df.empty:
		return 0
	value = df.iloc[0].get("count")
	try:
		return int(value) if value is not None else 0
	except (TypeError, ValueError):
		return 0

@st.cache_data(ttl=300, show_spinner=False)
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
	from src.core.categories import get_unified_category, get_category_icon
	value = str(category or "").strip()
	unified_id = get_unified_category(value)
	icon = get_category_icon(unified_id)
	label = CATEGORY_LABELS_EN.get(unified_id, "Other")
	return f"{icon} {label}"

def resolve_local_model_path() -> str | None:
	def is_trained_model_dir(path: Path) -> bool:
		if not path.exists() or not path.is_dir():
			return False
		if not (path / "config.json").exists():
			return False
		weight_files = ["model.safetensors", "pytorch_model.bin", "tf_model.h5"]
		return any((path / name).exists() for name in weight_files)

	candidates = [
		PROJECT_ROOT / "results" / "models" / "phobert_clickbait",
		PROJECT_ROOT / "results" / "models" / "visobert_clickbait",
		PROJECT_ROOT / "results" / "models" / "xlm_roberta_clickbait",
		PROJECT_ROOT / "models" / "phobert_clickbait",
	]
	for candidate in candidates:
		if is_trained_model_dir(candidate):
			return str(candidate)
	return None

def run_local_labeling(batch_size: int = 32, model_version: str = "phobert_v1.0") -> tuple[bool, str]:
	model_path = resolve_local_model_path()
	if not model_path:
		return (
			False,
			"No trained model found. A valid model directory must contain `config.json` and weights (`model.safetensors` or `pytorch_model.bin`).",
		)

	try:
		from src.scripts.pred_label import run_labeling

		run_labeling(
			model_path=model_path,
			model_version=model_version,
			batch_size=batch_size,
			show_samples=False,
		)
		cached_read_sql.clear()
		get_row_count.clear()
		get_distinct_values.clear()
		get_recent_articles.clear()
		get_latest_articles.clear()
		get_available_hot_topic_dates.clear()
		return True, f"Local labeling completed successfully using `{model_path}`. No Gemini API was used."
	except Exception as exc:  # noqa: BLE001
		return False, f"Labeling failed: {exc}"

def prepare_article_records(df: pd.DataFrame) -> list[dict]:
	"""Sanitize article DataFrame and return list of dict records."""
	if df is None or df.empty:
		return []
	df = df.copy()
	if "prediction_score" in df.columns:
		df["prediction_score"] = pd.to_numeric(df["prediction_score"], errors="coerce").fillna(0.0).clip(0.0, 1.0)
	else:
		df["prediction_score"] = 0.0
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

	if source and source != ALL_OPTION:
		clauses.append("source = ?")
		params.append(source)

	if category and category != ALL_OPTION:
		if category == 'khac':
			from src.core.categories import CATEGORY_MAP
			placeholders = ", ".join("?" for _ in CATEGORY_MAP.keys())
			clauses.append(f"(category NOT IN ({placeholders}) OR category IS NULL)")
			params.extend(CATEGORY_MAP.keys())
		else:
			from src.core.categories import get_raw_categories_for_unified
			raw_cats = get_raw_categories_for_unified(category)
			if raw_cats:
				placeholders = ", ".join("?" for _ in raw_cats)
				clauses.append(f"category IN ({placeholders})")
				params.extend(raw_cats)
			else:
				clauses.append("category = ?")
				params.append(category)

	if label and label != ALL_OPTION:
		if label == UNLABELED_OPTION:
			clauses.append("predicted_label IS NULL")
		else:
			clauses.append("predicted_label = ?")
			params.append(label)

	where_clause = " WHERE " + " AND ".join(clauses) if clauses else ""
	return where_clause, tuple(params)

@st.cache_data(ttl=300, show_spinner=False)
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

@st.cache_data(ttl=300, show_spinner=False)
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

@st.cache_data(ttl=300, show_spinner=False)
def get_available_hot_topic_dates() -> list[str]:
	"""Get all distinct dates from hot_topics."""
	df = cached_read_sql(
		"""
		SELECT DISTINCT DATE(created_at) AS topic_date
		FROM hot_topics
		WHERE created_at IS NOT NULL
		ORDER BY topic_date DESC
		"""
	)
	if df.empty:
		return []
	return [str(d) for d in df["topic_date"].tolist() if d]

def get_hot_topics_for_feed(hours: int, date_filter: str = LATEST_OPTION, limit: int = 10) -> pd.DataFrame:
	"""Return up to *limit* topics for a timeframe, backfilling from older snapshots if needed."""
	if date_filter != LATEST_OPTION:
		# Filter by specific date
		return uncached_read_sql(
			"""
			SELECT id, topic_name, keywords, article_count, timeframe, created_at
			FROM hot_topics
			WHERE timeframe = ? AND DATE(created_at) = ?
			ORDER BY created_at DESC, article_count DESC, id ASC
			LIMIT ?
			""",
			(hours, date_filter, limit),
		)

	latest_df = get_latest_hot_topics(hours)
	if latest_df.empty:
		# Fallback to get any topics for this timeframe if no active snapshot found
		latest_df = uncached_read_sql(
			"""
			SELECT id, topic_name, keywords, article_count, timeframe, created_at
			FROM hot_topics
			WHERE timeframe = ?
			ORDER BY created_at DESC, article_count DESC, id ASC
			LIMIT ?
			""",
			(hours, limit),
		)
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
			a.url, a.predicted_label, a.prediction_score,
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

def get_badge_html(label, score):
	"""Get badge HTML based on label"""
	if label == "clickbait":
		text = "⚠️ Clickbait"
		badge_class = "badge-clickbait"
	elif label == "non-clickbait":
		text = "✓ Verified"
		badge_class = "badge-safe"
	else:
		text = "? Unlabeled"
		badge_class = "badge-unlabeled"
	
	score_str = f" ({score:.0%})" if score and label in ["clickbait", "non-clickbait"] else ""
	return f'<span class="featured-badge {badge_class}">{text}{score_str}</span>'

def render_article_detail(article_id):
	"""Render detail page for a specific article"""
	article = get_article_by_id(article_id)

	if not article:
		st.error("Article not found.")
		if st.button("← Back"):
			st.session_state.selected_article_id = None
			clear_query_params()
			st.rerun()
		return

	if st.button("← Back to list", key="back_to_list_btn"):
		st.session_state.selected_article_id = None
		clear_query_params()
		st.rerun()

	title = html.escape(str(article.get("title", "")))
	source = html.escape(str(article.get("source", "")))
	category = html.escape(normalize_category_label(article.get("category", "")))
	published_at = html.escape(str(article.get("published_at", "")))
	crawled_at = html.escape(str(article.get("crawled_at", "")))
	content_text = str(article.get("content_text", "") or "").strip()
	summary = html.escape(str(article.get("summary", "") or ""))
	url = str(article.get("url", "") or "").strip()
	label = article.get("predicted_label", UNLABELED_OPTION)
	raw_score = article.get("prediction_score", 0)
	try:
		score = float(raw_score) if raw_score is not None else 0.0
	except (TypeError, ValueError):
		score = 0.0

	badge_html = get_badge_html(label, score)
	content_html = html.escape(content_text).replace("\n", "<br>") if content_text else "No full article content available."
	url_html = f'<div class="article-detail-url">🔗 <a href="{html.escape(url)}" target="_blank" rel="noopener noreferrer">Open original article</a></div>' if url else ""

	st.markdown(
		f"""
		<div class="detail-shell" style="margin-top: 15px;">
			<div class="article-detail">
				<div class="article-detail-meta"><b>{source}</b> · {category} · {published_at or crawled_at}</div>
				<h2 style="margin: 0 0 15px 0; font-size: clamp(24px, 2.5vw, 36px); line-height: 1.25; color: var(--text); font-weight: 800;">{title}</h2>
				<div style="margin-bottom: 15px;">{badge_html}</div>
				<div style="background: rgba(57, 166, 255, 0.10); padding: 15px; border-radius: var(--radius-md); border-left: 4px solid var(--accent); margin-bottom: 20px; border: 1px solid var(--panel-border);">
					<h4 style="margin: 0 0 5px 0; font-size: 14px; text-transform: uppercase; color: var(--muted-strong); font-weight: 700;">Quick Summary (AI)</h4>
					<p style="font-size: 14px; line-height: 1.6; color: var(--text); margin: 0;">{summary}</p>
				</div>
				<div class="article-detail-body" style="font-size: 15px; line-height: 1.8; color: var(--text);">{content_html}</div>
				{url_html}
			</div>
		</div>
		""",
		unsafe_allow_html=True,
	)

def render_topic_detail(topic_id: int):
	"""Render a dedicated page for a hot topic and its linked articles."""
	topic = get_hot_topic_by_id(topic_id)
	if not topic:
		st.error("Topic not found.")
		if st.button("← Back"):
			st.session_state.selected_topic_id = None
			st.session_state.current_view = "home"
			st.rerun()
		return

	articles_df = get_articles_by_topic_id(topic_id)

	if st.button("← Back to topics", key="back_to_topics_btn"):
		st.session_state.selected_topic_id = None
		st.session_state.current_view = "home"
		clear_query_params()
		st.rerun()

	st.markdown(
		f"""
		<div class="topic-shell" style="margin-top: 15px;">
			<div class="article-detail" style="padding: 20px;">
				<div class="article-detail-meta"><b>Hot Topic</b> · Timeframe {html.escape(str(topic.get('timeframe') or ''))}h · Snapshot {html.escape(str(topic.get('created_at') or ''))}</div>
				<h2 style="margin: 0 0 10px 0; font-size: clamp(24px, 2.5vw, 36px); color: var(--accent); font-weight: 800;">{html.escape(str(topic.get('topic_name') or ''))}</h2>
				<div style="font-size: 14px; color: var(--muted-strong); margin-top: 8px;"><b>Top keywords:</b> {html.escape(str(topic.get('keywords') or ''))}</div>
			</div>
		</div>
		""",
		unsafe_allow_html=True,
	)

	if articles_df.empty:
		st.info("No linked articles for this topic yet.")
		return

	st.markdown(f"<h3 style='margin: 25px 0 15px 0; font-size: 18px; font-weight: 700;'>Related articles ({len(articles_df):,})</h3>", unsafe_allow_html=True)
	
	for idx, article in enumerate(prepare_article_records(articles_df)):
		title = html.escape(str(article.get("title", "") or "(Untitled)"))
		summary = html.escape(str(article.get("summary", "") or "No summary available."))
		source = html.escape(str(article.get("source", "")))
		published_at = html.escape(str(article.get("published_at") or article.get("crawled_at") or ""))
		badge = get_badge_html(article.get("predicted_label"), article.get("prediction_score"))
		article_id = article.get("article_id")

		st.markdown(
			f"""
			<a href="?article_id={article_id}" target="_self" style="text-decoration: none; color: inherit; display: block;">
				<div class="detail-card" style="margin-bottom: 12px; background: var(--panel); border: 1px solid var(--panel-border); padding: 15px; border-radius: var(--radius-md); transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease; cursor: pointer;">
					<div class="detail-meta" style="font-size: 11px; font-weight: 700; color: var(--muted); text-transform: uppercase;">{source} · {published_at}</div>
					<div class="topic-card-title" style="font-size: 16px; font-weight: 700; margin-top: 5px; color: var(--text);">{title}</div>
					<div class="topic-card-summary" style="font-size: 13.5px; color: var(--muted-strong); margin-top: 8px; line-height: 1.5;">{summary}</div>
					<div style="margin-top: 10px;">{badge}</div>
				</div>
			</a>
			""",
			unsafe_allow_html=True,
		)

def render_article_grid_clickable(articles):
	"""Render article grid with clickable cards"""
	if not articles:
		return
	
	cols = st.columns(2)
	for idx, article in enumerate(articles):
		article_id = article.get("article_id")
		title = str(article.get("title", ""))
		summary = str(article.get("summary", ""))[:120] + "..." if len(str(article.get("summary", ""))) > 120 else str(article.get("summary", ""))
		source = str(article.get("source", ""))
		category = normalize_category_label(article.get("category", ""))
		badge = get_badge_html(article.get("predicted_label"), article.get("prediction_score"))
		
		with cols[idx % 2]:
			st.markdown(
				render_article_card_html(title, summary, source, category, badge, article_id),
				unsafe_allow_html=True
			)

def main():
	ensure_database()
	inject_styles()
	
	# Initialize session state keys
	if "selected_article_id" not in st.session_state:
		st.session_state.selected_article_id = None
	if "selected_topic_id" not in st.session_state:
		st.session_state.selected_topic_id = None
	if "current_view" not in st.session_state:
		st.session_state.current_view = "home"
	if "navigation_page" not in st.session_state:
		st.session_state.navigation_page = NAV_OVERVIEW
	if "last_page" not in st.session_state:
		st.session_state.last_page = NAV_OVERVIEW

	# Check query parameters for article_id or topic_id to handle clickable HTML cards
	qp_article_id = get_query_param("article_id")
	if qp_article_id:
		st.session_state.selected_article_id = qp_article_id

	qp_topic_id = get_query_param("topic_id")
	if qp_topic_id:
		st.session_state.selected_topic_id = int(qp_topic_id)
		st.session_state.current_view = "topic_detail"
		st.session_state.navigation_page = NAV_TOPICS

	# Render Topbar Navigation
	col_logo, col_nav = st.columns([1, 2.2])
	with col_logo:
		st.markdown(
			"""
			<div style="padding-top: 5px; margin-bottom: 20px;">
				<h1 style="margin: 0; color: var(--accent); font-size: 28px; font-weight: 800; line-height: 1.2;">VnNew<span style="color: var(--text);">AI</span></h1>
				<p style="font-size: 10px; color: var(--muted); margin: 0; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;">AI News Analysis System</p>
			</div>
			""",
			unsafe_allow_html=True,
		)
	with col_nav:
		selected_page = st.radio(
			"Navigation menu",
			[NAV_OVERVIEW, NAV_ARTICLES, NAV_TOPICS],
			key="navigation_page",
			horizontal=True,
			label_visibility="collapsed"
		)
	st.markdown("<hr style='border: 0; border-top: 1px solid var(--panel-border); margin: 0 0 25px 0;'>", unsafe_allow_html=True)
	
	# Reset states on page change
	if st.session_state.last_page != selected_page:
		st.session_state.selected_article_id = None
		st.session_state.selected_topic_id = None
		st.session_state.current_view = "home"
		st.session_state.last_page = selected_page
		clear_query_params()
		st.rerun()

	# Route Detail views first
	if st.session_state.selected_article_id:
		render_article_detail(st.session_state.selected_article_id)
		return

	if st.session_state.current_view == "topic_detail" and st.session_state.selected_topic_id is not None:
		render_topic_detail(st.session_state.selected_topic_id)
		return

	# PAGE 1: OVERVIEW
	if selected_page == NAV_OVERVIEW:
		st.markdown("<h2 class='dashboard-title'>System Overview</h2>", unsafe_allow_html=True)
		st.markdown("<p class='dashboard-subtitle'>Key metrics, latest articles, and AI-detected hot topics.</p>", unsafe_allow_html=True)
		with st.expander("Actions", expanded=False):
			st.caption("Run local clickbait labeling from this dashboard. Gemini API is not required.")
			col_cfg_1, col_cfg_2 = st.columns(2)
			with col_cfg_1:
				label_batch_size = int(
					st.number_input(
						"Batch size",
						min_value=1,
						max_value=512,
						value=32,
						step=1,
						key="ov_label_batch_size",
					)
				)
			with col_cfg_2:
				label_model_version = st.text_input(
					"Model version",
					value="phobert_v1.0",
					key="ov_label_model_version",
				).strip() or "phobert_v1.0"

			if st.button("Run local labeling now", key="ov_run_local_labeling_btn"):
				with st.spinner("Running local labeling..."):
					ok, message = run_local_labeling(
						batch_size=label_batch_size,
						model_version=label_model_version,
					)
				if ok:
					st.success(message)
					st.rerun()
				else:
					st.error(message)
		
		# Fetch Stats (All-time stats to represent the whole database)
		stats = get_overview_stats(0, ALL_OPTION, ALL_OPTION, ALL_OPTION)
			
		db_total_articles = get_row_count("articles")
		db_hot_topics = get_row_count("hot_topics")
		labeled = stats['labeled_count'] or 0
		clickbait = stats['clickbait_count'] or 0
		ratio = (clickbait / labeled * 100) if labeled > 0 else 0.0
		
		# KPI cards
		st.markdown("<h3 style='margin: 20px 0 10px 0; font-size: 16px; font-weight: 700; text-transform: uppercase; color: var(--muted); letter-spacing: 0.05em;'>Key Metrics</h3>", unsafe_allow_html=True)
		col_m1, col_m2, col_m3, col_m4 = st.columns(4)
		with col_m1:
			st.metric("Total Stored Articles", f"{db_total_articles:,}", help="Total number of crawled articles")
		with col_m2:
			st.metric("AI-Labeled Articles", f"{labeled:,}", help="Articles labeled by the clickbait classifier")
		with col_m3:
			st.metric("Detected Clickbait", f"{clickbait:,}", help="Articles predicted as clickbait")
		with col_m4:
			st.metric("Clickbait Rate", f"{ratio:.1f}%", help="Clickbait share among labeled articles")
			
		st.markdown("<hr style='border: 0; border-top: 1px solid var(--panel-border); margin: 25px 0;'>", unsafe_allow_html=True)
		
		# Split View: Latest News vs Hot Topics
		col_left, col_right = st.columns([1.6, 1], gap="large")
		
		with col_left:
			st.markdown("<h3 class='section-title'>LATEST NEWS</h3>", unsafe_allow_html=True)
			latest_articles = get_latest_articles(limit=5)
			if latest_articles.empty:
				st.info("No articles found in the database yet.")
			else:
				for idx, article in enumerate(prepare_article_records(latest_articles)):
					title = html.escape(str(article.get("title", ""))[:100])
					summary = html.escape(str(article.get("summary", ""))[:180]) + "..." if len(str(article.get("summary", ""))) > 180 else html.escape(str(article.get("summary", "")))
					source = html.escape(str(article.get("source", "")))
					category = html.escape(normalize_category_label(article.get("category", "")))
					badge = get_badge_html(article.get("predicted_label"), article.get("prediction_score"))
					article_id = article.get("article_id")
					
					st.markdown(
						render_article_card_html(title, summary, source, category, badge, article_id),
						unsafe_allow_html=True
					)
							
		with col_right:
			col_title, col_sel = st.columns([1.5, 1])
			with col_title:
				st.markdown("<h3 class='section-title' style='margin-top: 0;'>HOT TOPICS</h3>", unsafe_allow_html=True)
			with col_sel:
				ov_hot_timeframe = st.selectbox(
					"Hot topic timeframe",
					options=list(HOT_TOPIC_TIMEFRAME_OPTIONS.keys()),
					index=2,
					key="ov_hot_timeframe_selector",
					label_visibility="collapsed"
				)
			
			hours_val = HOT_TOPIC_TIMEFRAME_OPTIONS.get(ov_hot_timeframe, 24)
			hot_topics_feed = get_hot_topics_for_feed(hours_val, limit=5)
			if hot_topics_feed.empty:
				st.info(f"No hot topics detected in the last {ov_hot_timeframe}.")
			else:
				for idx, topic in enumerate(hot_topics_feed.to_dict("records")):
					topic_id = topic.get("id")
					topic_name = html.escape(str(topic.get("topic_name", "") or "(Untitled topic)"))
					article_count = int(topic.get("article_count") or 0)
					keywords = html.escape(str(topic.get("keywords", "") or ""))
					
					st.markdown(
						f"""
						<a href="?topic_id={topic_id}" target="_self" style="text-decoration: none; color: inherit; display: block;">
							<div class="topic-card" style="margin-bottom: 12px; background: var(--panel); padding: 15px; border: 1px solid var(--panel-border); border-radius: var(--radius-md); transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease; cursor: pointer;">
								<div class="topic-card-title" style="font-size: 15px; font-weight: 700; color: var(--accent);">{topic_name}</div>
								<div class="topic-card-meta" style="font-size: 11px; font-weight: 700; color: var(--muted); margin-top: 5px; text-transform: uppercase;">🔥 {article_count} articles</div>
								<div style="font-size: 12.5px; color: var(--muted-strong); margin-top: 6px; line-height: 1.4;"><b>Keywords:</b> {keywords}</div>
							</div>
						</a>
						""",
						unsafe_allow_html=True
					)

	# PAGE 2: ARTICLE EXPLORER
	elif selected_page == NAV_ARTICLES:
		st.markdown("<h2 class='dashboard-title'>Article Explorer</h2>", unsafe_allow_html=True)
		st.markdown("<p class='dashboard-subtitle'>Filter news by timeframe, source, category, and clickbait prediction labels.</p>", unsafe_allow_html=True)
		
		search_query = st.text_input("🔍 Search in title or summary", placeholder="Enter keyword...", key="exp_search_query")
		
		# Filters Panel
		col_f1, col_f2, col_f3, col_f4 = st.columns(4)
		with col_f1:
			time_filter = st.selectbox(
				"Time window",
				options=[ALL_OPTION] + list(TIMEFRAME_OPTIONS.keys()),
				index=4,
				key="exp_time_filter"
			)
		with col_f2:
			sources = [ALL_OPTION] + get_distinct_values("source")
			source_filter = st.selectbox(
				"News source",
				options=sources,
				index=0,
				key="exp_source_filter"
			)
		with col_f3:
			from src.core.categories import UNIFIED_CATEGORIES, get_category_icon
			categories = [ALL_OPTION] + list(UNIFIED_CATEGORIES.keys())
			
			def format_category_option(cat_id: str) -> str:
				if cat_id == ALL_OPTION:
					return ALL_OPTION
				return f"{get_category_icon(cat_id)} {CATEGORY_LABELS_EN.get(cat_id, 'Other')}"

			category_filter = st.selectbox(
				"Category",
				options=categories,
				index=0,
				format_func=format_category_option,
				key="exp_category_filter"
			)
		with col_f4:
			label_filter = st.selectbox(
				"Clickbait label",
				options=LABEL_OPTIONS,
				index=0,
				key="exp_label_filter"
			)
		
		# Query articles based on filters
		hours = TIMEFRAME_OPTIONS.get(time_filter, 0) if time_filter != ALL_OPTION else 0
		articles_df = get_recent_articles(hours, source_filter, category_filter, label_filter, limit=300)
		
		if search_query.strip():
			q = search_query.strip().lower()
			mask = (
				articles_df["title"].fillna("").str.lower().str.contains(q)
				| articles_df["summary"].fillna("").str.lower().str.contains(q)
			)
			articles_df = articles_df[mask]
			
		if articles_df.empty:
			st.info("No articles match the current filters.")
		else:
			st.markdown(f"<p style='color: var(--muted-strong); font-weight: 600; margin-bottom: 15px;'>Found <b>{len(articles_df):,}</b> matching articles</p>", unsafe_allow_html=True)
			render_article_grid_clickable(prepare_article_records(articles_df.head(60)))

	# PAGE 3: HOT TOPICS
	elif selected_page == NAV_TOPICS:
		st.markdown("<h2 class='dashboard-title'>Trending News Topics</h2>", unsafe_allow_html=True)
		st.markdown("<p class='dashboard-subtitle'>Automatic topic clustering over recent articles to surface major events.</p>", unsafe_allow_html=True)
		
		topic_search_query = st.text_input("🔍 Search by topic name or keyword", placeholder="Enter topic name or keyword...", key="ht_search_query")
		
		col_ht1, col_ht2 = st.columns(2)
		with col_ht1:
			hot_timeframe = st.selectbox(
				"Clustering timeframe",
				options=list(HOT_TOPIC_TIMEFRAME_OPTIONS.keys()),
				index=2,
				key="ht_timeframe_selector"
			)
		with col_ht2:
			available_dates = [LATEST_OPTION] + get_available_hot_topic_dates()
			hot_date_filter = st.selectbox(
				"Snapshot date",
				options=available_dates,
				index=0,
				key="ht_date_selector"
			)
			
		hours_val = HOT_TOPIC_TIMEFRAME_OPTIONS.get(hot_timeframe, 24)
		hot_topics_feed = get_hot_topics_for_feed(hours_val, date_filter=hot_date_filter, limit=20)
		
		if topic_search_query.strip():
			q = topic_search_query.strip().lower()
			mask = (
				hot_topics_feed["topic_name"].fillna("").str.lower().str.contains(q)
				| hot_topics_feed["keywords"].fillna("").str.lower().str.contains(q)
			)
			hot_topics_feed = hot_topics_feed[mask]
			
		st.markdown("<hr style='border: 0; border-top: 1px solid var(--panel-border); margin: 20px 0;'>", unsafe_allow_html=True)
		
		if hot_topics_feed.empty:
			st.info("No matching hot topic clusters were found.")
		else:
			st.markdown(f"<p style='color: var(--muted-strong); font-weight: 600; margin-bottom: 15px;'>Detected/Found <b>{len(hot_topics_feed)}</b> prominent hot topics</p>", unsafe_allow_html=True)
			
			for idx, topic in enumerate(hot_topics_feed.to_dict("records")):
				topic_id = topic.get("id")
				title = html.escape(str(topic.get("topic_name", "") or "(Untitled topic)"))
				article_count = int(topic.get("article_count") or 0)
				keywords = html.escape(str(topic.get("keywords", "") or ""))
				created_at = html.escape(str(topic.get("created_at") or ""))
				
				st.markdown(
					f"""
					<a href="?topic_id={topic_id}" target="_self" style="text-decoration: none; color: inherit; display: block;">
						<div class="topic-card" style="margin-bottom: 15px; padding: 20px; background: var(--panel); border: 1px solid var(--panel-border); border-radius: var(--radius-lg); transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease; cursor: pointer;">
							<div style="display: flex; justify-content: space-between; align-items: start; flex-wrap: wrap; gap: 10px;">
								<div class="topic-card-title" style="font-size: 18px; color: var(--accent); font-weight: 800;">{title}</div>
								<span class="featured-badge badge-safe" style="font-size: 12px; font-weight: 700; background: rgba(79,70,229,0.08); color: var(--accent); border: 1px solid rgba(79,70,229,0.2);">🔥 {article_count} articles</span>
							</div>
							<div class="topic-card-summary" style="margin-top: 10px; font-size: 14px; color: var(--text);">
								<strong>Top keywords:</strong> <span style="background: rgba(57, 166, 255, 0.10); padding: 2px 8px; border-radius: 4px; font-weight: 600; color: var(--muted-strong); border: 1px solid var(--panel-border);">{keywords}</span>
							</div>
							<div class="topic-card-meta" style="margin-top: 12px; font-size: 11px; color: var(--muted);">
								<span>Captured at: {created_at}</span>
							</div>
						</div>
					</a>
					""",
					unsafe_allow_html=True
				)

if __name__ == "__main__":
	main()
