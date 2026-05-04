from __future__ import annotations

import html


def premium_dashboard_styles() -> str:
	return """
<style>
:root {
	--bg: #081018;
	--panel: rgba(16, 24, 38, 0.92);
	--panel-strong: rgba(19, 29, 45, 0.98);
	--panel-border: rgba(255, 255, 255, 0.08);
	--panel-border-strong: rgba(255, 255, 255, 0.14);
	--text: #edf4ff;
	--muted: #9aa8ba;
	--muted-strong: #c7d1de;
	--accent: #ff7a59;
	--accent-strong: #ff9d7f;
	--accent-soft: rgba(255, 122, 89, 0.12);
	--safe: #57d39a;
	--safe-soft: rgba(87, 211, 154, 0.12);
	--shadow: 0 24px 60px rgba(0, 0, 0, 0.35);
	--shadow-soft: 0 14px 34px rgba(0, 0, 0, 0.2);
	--radius-xl: 28px;
	--radius-lg: 20px;
	--radius-md: 16px;
}

html, body, .stApp {
	background:
		radial-gradient(circle at top left, rgba(255, 122, 89, 0.18), transparent 30%),
		radial-gradient(circle at top right, rgba(87, 211, 154, 0.12), transparent 24%),
		linear-gradient(180deg, #09111a 0%, #081018 45%, #071019 100%) !important;
	color: var(--text) !important;
	font-family: "Segoe UI", "Aptos", "Inter", sans-serif;
}

.stApp > header,
[data-testid="stToolbar"],
[data-testid="stSidebar"],
[data-testid="stSidebarContent"],
[data-testid="stAppViewContainer"] {
	background: transparent !important;
}

.block-container {
	padding-top: 1rem !important;
	padding-bottom: 2rem !important;
}

a {
	color: var(--accent-strong);
	text-decoration: none;
}

a:hover {
	text-decoration: underline;
}

* {
	box-sizing: border-box;
}

.dashboard-shell {
	position: relative;
	z-index: 1;
	max-width: 1480px;
	margin: 0 auto;
}

.dashboard-hero {
	position: relative;
	overflow: hidden;
	padding: 28px;
	border-radius: var(--radius-xl);
	background:
		linear-gradient(135deg, rgba(18, 29, 44, 0.92), rgba(12, 18, 28, 0.88)),
		radial-gradient(circle at top right, rgba(255, 122, 89, 0.18), transparent 32%),
		radial-gradient(circle at bottom left, rgba(87, 211, 154, 0.12), transparent 28%);
	border: 1px solid var(--panel-border);
	box-shadow: var(--shadow);
	backdrop-filter: blur(18px);
	margin-bottom: 20px;
}

.dashboard-brand {
	display: flex;
	flex-direction: column;
	gap: 10px;
}

.dashboard-kicker {
	display: inline-flex;
	align-items: center;
	gap: 8px;
	width: fit-content;
	padding: 7px 12px;
	border-radius: 999px;
	background: rgba(255, 255, 255, 0.06);
	border: 1px solid rgba(255, 255, 255, 0.08);
	color: var(--muted-strong);
	font-size: 12px;
	font-weight: 700;
	letter-spacing: 0.08em;
	text-transform: uppercase;
}

.dashboard-title {
	margin: 0;
	font-size: clamp(32px, 4vw, 52px);
	line-height: 1.02;
	font-weight: 900;
	letter-spacing: -0.04em;
	color: var(--text);
}

.dashboard-subtitle {
	max-width: 840px;
	margin: 0;
	color: var(--muted);
	font-size: 15px;
	line-height: 1.7;
}

.dashboard-hero-grid {
	display: grid;
	grid-template-columns: 1.8fr 1fr;
	gap: 18px;
	margin-top: 22px;
}

.hero-panel,
.metric-panel,
.filter-panel,
.article-shell,
.detail-shell,
.topic-shell,
.search-shell {
	background: var(--panel);
	border: 1px solid var(--panel-border);
	border-radius: var(--radius-lg);
	box-shadow: var(--shadow-soft);
	backdrop-filter: blur(14px);
}

.hero-panel {
	padding: 18px;
}

.hero-panel-title,
.section-title,
.sidebar-title,
.topic-title,
.search-title,
.detail-title {
	font-size: 12px;
	font-weight: 800;
	letter-spacing: 0.14em;
	text-transform: uppercase;
	color: var(--muted);
}

.hero-panel-copy {
	margin: 0;
	color: var(--text);
	font-size: 18px;
	line-height: 1.55;
	font-weight: 650;
}

.hero-panel-grid {
	display: grid;
	grid-template-columns: repeat(2, minmax(0, 1fr));
	gap: 12px;
	margin-top: 18px;
}

.micro-card {
	padding: 14px;
	border-radius: 18px;
	background: rgba(255, 255, 255, 0.04);
	border: 1px solid rgba(255, 255, 255, 0.06);
}

.micro-card-label,
.metric-label {
	color: var(--muted);
	font-size: 12px;
	font-weight: 700;
	text-transform: uppercase;
	letter-spacing: 0.08em;
}

.micro-card-value,
.metric-value {
	margin-top: 6px;
	color: var(--text);
	font-size: 20px;
	font-weight: 800;
}

.micro-card-note,
.metric-help {
	margin-top: 6px;
	color: var(--muted);
	font-size: 13px;
	line-height: 1.5;
}

.control-rail,
.metrics-row,
.article-layout,
.hero-panel-grid,
.panel-stack,
.sidebar-stack,
.topic-stack,
.search-stack {
	display: grid;
	gap: 14px;
}

.control-rail {
	grid-template-columns: 1.2fr 1fr 1fr;
	margin: 20px 0 8px;
}

.metrics-row {
	grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
	margin: 20px 0 18px;
}

.metric-panel {
	padding: 16px 18px;
}

.article-layout {
	grid-template-columns: minmax(0, 1.8fr) minmax(320px, 1fr);
	align-items: start;
}

.article-shell,
.detail-shell,
.topic-shell,
.search-shell {
	padding: 18px;
}

.section-title {
	margin: 34px 0 16px;
	font-size: 16px;
}

.section-title::after {
	content: "";
	display: block;
	width: 82px;
	height: 3px;
	margin-top: 8px;
	border-radius: 999px;
	background: linear-gradient(90deg, var(--accent), rgba(255, 122, 89, 0.1));
}

.section-subtitle {
	color: var(--muted);
	font-size: 13px;
	margin: -8px 0 16px;
}

.article-featured,
.article-card,
.topic-card,
.search-card,
.detail-card,
.sidebar-item {
	position: relative;
	overflow: hidden;
	padding: 18px;
	border-radius: var(--radius-md);
	background: linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
	border: 1px solid rgba(255,255,255,0.08);
	box-shadow: 0 10px 24px rgba(0, 0, 0, 0.14);
	transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
}

.article-featured:hover,
.article-card:hover,
.topic-card:hover,
.search-card:hover,
.detail-card:hover,
.sidebar-item:hover {
	transform: translateY(-2px);
	border-color: var(--panel-border-strong);
	box-shadow: 0 16px 34px rgba(0, 0, 0, 0.22);
}

.article-card-title,
.search-card-title,
.topic-card-title,
.sidebar-item-title {
	margin: 0;
	color: var(--text);
	font-size: 15px;
	font-weight: 800;
	line-height: 1.45;
}

.article-card-summary,
.search-card-summary,
.topic-card-summary {
	margin-top: 10px;
	color: var(--muted);
	font-size: 14px;
	line-height: 1.6;
}

.article-card-meta,
.search-card-meta,
.topic-card-meta,
.sidebar-item-meta,
.detail-meta {
	display: flex;
	flex-wrap: wrap;
	gap: 8px 12px;
	margin-top: 10px;
	color: var(--muted-strong);
	font-size: 12px;
	font-weight: 700;
	text-transform: uppercase;
	letter-spacing: 0.05em;
}

.featured-badge,
.status-badge {
	display: inline-flex;
	align-items: center;
	gap: 8px;
	padding: 8px 12px;
	border-radius: 999px;
	font-size: 12px;
	font-weight: 800;
	letter-spacing: 0.04em;
	text-transform: uppercase;
}

.badge-clickbait {
	background: var(--accent-soft);
	color: #ffb19b;
	border: 1px solid rgba(255, 122, 89, 0.22);
}

.badge-safe {
	background: var(--safe-soft);
	color: #a9f0c9;
	border: 1px solid rgba(87, 211, 154, 0.22);
}

.badge-unlabeled {
	background: rgba(255, 255, 255, 0.06);
	color: var(--muted-strong);
	border: 1px solid rgba(255, 255, 255, 0.12);
}

.article-detail,
.article-detail-page {
	padding: 22px;
	border-radius: var(--radius-lg);
	background: var(--panel-strong);
	border: 1px solid var(--panel-border);
	box-shadow: var(--shadow-soft);
}

.article-detail-meta,
.article-detail-page .article-detail-meta {
	color: var(--muted-strong);
	font-size: 12px;
	font-weight: 800;
	letter-spacing: 0.05em;
	text-transform: uppercase;
	margin-bottom: 14px;
}

.article-detail-body {
	margin-top: 18px;
	color: var(--text);
	font-size: 16px;
	line-height: 1.8;
	white-space: pre-wrap;
}

.article-detail-url {
	margin-top: 18px;
	color: var(--muted);
	font-weight: 700;
}

.stButton button {
	border-radius: 999px !important;
	border: 1px solid rgba(255, 255, 255, 0.10) !important;
	background: linear-gradient(135deg, rgba(255, 122, 89, 0.95), rgba(255, 146, 107, 0.88)) !important;
	color: #fff !important;
	font-weight: 800 !important;
	box-shadow: 0 10px 24px rgba(255, 122, 89, 0.24);
	transition: transform 160ms ease, box-shadow 160ms ease, filter 160ms ease;
}

.stButton button:hover {
	transform: translateY(-1px);
	filter: brightness(1.02);
	box-shadow: 0 14px 28px rgba(255, 122, 89, 0.28);
}

.stMetric {
	background: transparent !important;
}

[data-testid="stMetricValue"] {
	color: var(--text) !important;
	font-weight: 900 !important;
}

@media (max-width: 1100px) {
	.dashboard-hero-grid,
	.article-layout,
	.control-rail {
		grid-template-columns: 1fr;
	}

	.hero-panel-grid {
		grid-template-columns: 1fr;
	}
}

@media (max-width: 760px) {
	.dashboard-hero,
	.article-shell,
	.detail-shell,
	.topic-shell,
	.search-shell,
	.metric-panel,
	.filter-panel {
		padding: 14px;
	}

	.dashboard-title {
		font-size: 30px;
	}

	.metrics-row {
		grid-template-columns: 1fr 1fr;
	}

	.article-card,
	.topic-card,
	.search-card,
	.detail-card {
		padding: 16px;
	}
}

@media (prefers-reduced-motion: reduce) {
	*, *::before, *::after {
		animation-duration: 0.01ms !important;
		animation-iteration-count: 1 !important;
		transition-duration: 0.01ms !important;
		scroll-behavior: auto !important;
	}
}
</style>
"""


def render_dashboard_hero(date_label: str, mode_label: str, total_articles: int, hot_topics: int) -> str:
	return f"""
	<div class="dashboard-hero">
		<div class="dashboard-brand">
			<div class="dashboard-kicker">AI News Intelligence · Live editorial dashboard</div>
			<h1 class="dashboard-title">VnNew<span style="color: var(--accent-strong);">AI</span></h1>
			<p class="dashboard-subtitle">A premium newsroom interface for exploring Vietnamese news, spotting clickbait risk, and tracking hot topics in one continuous reading surface.</p>
		</div>
		<div class="dashboard-hero-grid">
			<div class="hero-panel">
				<div class="hero-panel-title">Current session</div>
				<p class="hero-panel-copy">{html.escape(mode_label)} view is active with a curated, high-contrast reading layout designed for fast scanning and deeper drill-down.</p>
				<div class="hero-panel-grid">
					<div class="micro-card">
						<div class="micro-card-label">Today</div>
						<div class="micro-card-value">{html.escape(date_label)}</div>
						<div class="micro-card-note">Editorial snapshot updated for the current session.</div>
					</div>
					<div class="micro-card">
						<div class="micro-card-label">Coverage</div>
						<div class="micro-card-value">Live index</div>
						<div class="micro-card-note">Connected to the latest article dataset.</div>
					</div>
					<div class="micro-card">
						<div class="micro-card-label">Hot topics</div>
						<div class="micro-card-value">Topic feed</div>
						<div class="micro-card-note">Curated topic snapshots are ready for drill-down.</div>
					</div>
					<div class="micro-card">
						<div class="micro-card-label">Experience</div>
						<div class="micro-card-value">Premium UI</div>
						<div class="micro-card-note">Glass panels, sharper hierarchy, and richer interactions.</div>
					</div>
				</div>
			</div>
			<div class="hero-panel">
				<div class="hero-panel-title">Reading mode</div>
				<p class="hero-panel-copy">Use the controls below to move between article discovery and hot-topic analysis without losing context.</p>
				<div class="panel-stack" style="margin-top: 18px;">
					<div class="micro-card">
						<div class="micro-card-label">Mode</div>
						<div class="micro-card-value">{html.escape(mode_label)}</div>
					</div>
					<div class="micro-card">
						<div class="micro-card-label">Dashboard style</div>
						<div class="micro-card-value">Newsroom dark</div>
					</div>
				</div>
			</div>
		</div>
	</div>
	"""


def render_article_card_html(title: str, summary: str, source: str, category: str, badge_html: str, article_id: str | int | None) -> str:
	article_ref = html.escape(str(article_id or ""))
	return f"""
	<div class="article-card" data-article-id="{article_ref}">
		<div class="article-card-title">{html.escape(title)}</div>
		<div class="article-card-meta"><span>{html.escape(source)}</span><span>{html.escape(category)}</span></div>
		<div class="article-card-summary">{html.escape(summary)}</div>
		<div style="margin-top: 12px;">{badge_html}</div>
	</div>
	"""


def render_topic_card_html(title: str, summary: str, topic_meta: str) -> str:
	return f"""
	<div class="topic-card">
		<div class="topic-card-title">{html.escape(title)}</div>
		<div class="topic-card-meta">{html.escape(topic_meta)}</div>
		<div class="topic-card-summary">{html.escape(summary)}</div>
	</div>
	"""
