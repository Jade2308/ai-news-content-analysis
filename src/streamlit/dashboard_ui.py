from __future__ import annotations

import html


def premium_dashboard_styles() -> str:
	return """
<style>
:root {
	--bg: #f8fafc;
	--panel: #ffffff;
	--panel-strong: #ffffff;
	--panel-border: #e2e8f0;
	--panel-border-strong: #cbd5e1;
	--text: #0f172a;
	--muted: #64748b;
	--muted-strong: #475569;
	--accent: #4f46e5;
	--accent-strong: #4338ca;
	--accent-soft: rgba(79, 70, 229, 0.08);
	--safe: #059669;
	--safe-soft: rgba(5, 150, 105, 0.08);
	--shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.05);
	--shadow-soft: 0 4px 6px -1px rgba(0, 0, 0, 0.03), 0 2px 4px -2px rgba(0, 0, 0, 0.03);
	--radius-xl: 20px;
	--radius-lg: 16px;
	--radius-md: 12px;
}

html, body, .stApp {
	background:
		radial-gradient(circle at top left, rgba(79, 70, 229, 0.04), transparent 30%),
		radial-gradient(circle at top right, rgba(5, 150, 105, 0.03), transparent 24%),
		#f8fafc !important;
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
	padding-top: 3rem !important;
	padding-bottom: 2rem !important;
}

[data-testid="stHeader"] {
	background: transparent !important;
	height: 0 !important;
}

a {
	color: var(--accent);
	text-decoration: none;
	font-weight: 600;
}

a:hover {
	color: var(--accent-strong);
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
	background: #ffffff;
	border: 1px solid var(--panel-border);
	box-shadow: var(--shadow);
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
	padding: 6px 12px;
	border-radius: 999px;
	background: var(--accent-soft);
	border: 1px solid rgba(79, 70, 229, 0.15);
	color: var(--accent);
	font-size: 11px;
	font-weight: 700;
	letter-spacing: 0.08em;
	text-transform: uppercase;
}

.dashboard-title {
	margin: 0;
	font-size: clamp(32px, 4vw, 48px);
	line-height: 1.05;
	font-weight: 800;
	letter-spacing: -0.03em;
	color: var(--text);
}

.dashboard-subtitle {
	max-width: 840px;
	margin: 0;
	color: var(--muted);
	font-size: 15px;
	line-height: 1.6;
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
	letter-spacing: 0.12em;
	text-transform: uppercase;
	color: var(--muted);
}

.hero-panel-copy {
	margin: 0;
	color: var(--text);
	font-size: 17px;
	line-height: 1.5;
	font-weight: 600;
}

.hero-panel-grid {
	display: grid;
	grid-template-columns: repeat(2, minmax(0, 1fr));
	gap: 12px;
	margin-top: 18px;
}

.micro-card {
	padding: 14px;
	border-radius: 14px;
	background: #f8fafc;
	border: 1px solid var(--panel-border);
}

.micro-card-label,
.metric-label {
	color: var(--muted);
	font-size: 11px;
	font-weight: 700;
	text-transform: uppercase;
	letter-spacing: 0.08em;
}

.micro-card-value,
.metric-value {
	margin-top: 4px;
	color: var(--text);
	font-size: 18px;
	font-weight: 700;
}

.micro-card-note,
.metric-help {
	margin-top: 4px;
	color: var(--muted);
	font-size: 12px;
	line-height: 1.4;
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
	width: 60px;
	height: 3px;
	margin-top: 8px;
	border-radius: 999px;
	background: linear-gradient(90deg, var(--accent), rgba(79, 70, 229, 0.1));
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
	background: #ffffff;
	border: 1px solid var(--panel-border);
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.02);
	transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
}

.article-featured:hover,
.article-card:hover,
.topic-card:hover,
.search-card:hover,
.detail-card:hover,
.sidebar-item:hover {
	transform: translateY(-2px);
	border-color: rgba(79, 70, 229, 0.2);
	box-shadow: 0 8px 20px rgba(79, 70, 229, 0.08);
}

.article-card-title,
.search-card-title,
.topic-card-title,
.sidebar-item-title {
	margin: 0;
	color: var(--text);
	font-size: 15px;
	font-weight: 700;
	line-height: 1.4;
}

.article-card-summary,
.search-card-summary,
.topic-card-summary {
	margin-top: 8px;
	color: var(--muted-strong);
	font-size: 13.5px;
	line-height: 1.5;
}

.article-card-meta,
.search-card-meta,
.topic-card-meta,
.sidebar-item-meta,
.detail-meta {
	display: flex;
	flex-wrap: wrap;
	gap: 6px 12px;
	margin-top: 8px;
	color: var(--muted);
	font-size: 11px;
	font-weight: 700;
	text-transform: uppercase;
	letter-spacing: 0.05em;
}

.featured-badge,
.status-badge {
	display: inline-flex;
	align-items: center;
	gap: 6px;
	padding: 4px 10px;
	border-radius: 999px;
	font-size: 11px;
	font-weight: 700;
	letter-spacing: 0.02em;
	text-transform: uppercase;
}

.badge-clickbait {
	background: rgba(239, 68, 68, 0.08);
	color: #dc2626;
	border: 1px solid rgba(239, 68, 68, 0.2);
}

.badge-safe {
	background: var(--safe-soft);
	color: var(--safe);
	border: 1px solid rgba(5, 150, 105, 0.2);
}

.badge-unlabeled {
	background: rgba(100, 116, 139, 0.08);
	color: #475569;
	border: 1px solid rgba(100, 116, 139, 0.2);
}

.article-detail,
.article-detail-page {
	padding: 22px;
	border-radius: var(--radius-lg);
	background: #ffffff;
	border: 1px solid var(--panel-border);
	box-shadow: var(--shadow);
}

.article-detail-meta,
.article-detail-page .article-detail-meta {
	color: var(--muted);
	font-size: 11px;
	font-weight: 700;
	letter-spacing: 0.05em;
	text-transform: uppercase;
	margin-bottom: 12px;
}

.article-detail-body {
	margin-top: 16px;
	color: var(--text);
	font-size: 15px;
	line-height: 1.7;
	white-space: pre-wrap;
}

.article-detail-url {
	margin-top: 18px;
	color: var(--muted);
	font-weight: 700;
}

.stButton button {
	border-radius: 999px !important;
	border: none !important;
	background: var(--accent) !important;
	color: #fff !important;
	font-weight: 700 !important;
	box-shadow: 0 4px 12px rgba(79, 70, 229, 0.15) !important;
	transition: transform 160ms ease, box-shadow 160ms ease, filter 160ms ease !important;
}

.stButton button:hover {
	transform: translateY(-1px) !important;
	filter: brightness(1.05) !important;
	box-shadow: 0 6px 16px rgba(79, 70, 229, 0.25) !important;
}

.stMetric {
	background: #ffffff !important;
	border: 1px solid var(--panel-border) !important;
	border-radius: var(--radius-md) !important;
	padding: 12px 16px !important;
	box-shadow: var(--shadow-soft) !important;
}

[data-testid="stMetricValue"] {
	color: var(--text) !important;
	font-weight: 800 !important;
	font-size: 24px !important;
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

/* Hide Streamlit Sidebar elements completely */
[data-testid="stSidebar"] {
	display: none !important;
}
[data-testid="stSidebarCollapseButton"] {
	display: none !important;
}

/* Premium Topbar Navigation styling */
div[role="radiogroup"] {
	display: flex !important;
	flex-direction: row !important;
	justify-content: flex-end !important;
	gap: 12px !important;
	background: transparent !important;
	border: none !important;
	padding: 5px 0 !important;
}

div[role="radiogroup"] label {
	background: #ffffff !important;
	border: 1px solid var(--panel-border) !important;
	padding: 10px 20px !important;
	border-radius: var(--radius-md) !important;
	color: var(--muted-strong) !important;
	font-weight: 700 !important;
	font-size: 14px !important;
	transition: all 180ms cubic-bezier(0.4, 0, 0.2, 1) !important;
	cursor: pointer !important;
	margin: 0 !important;
	box-shadow: var(--shadow-soft) !important;
	display: inline-flex !important;
	align-items: center !important;
	justify-content: center !important;
}

div[role="radiogroup"] label:hover {
	background: #f8fafc !important;
	border-color: rgba(79, 70, 229, 0.3) !important;
	color: var(--accent) !important;
}

div[role="radiogroup"] label:hover * {
	color: var(--accent) !important;
}

/* Selected Tab styling */
div[role="radiogroup"] label:has(input[type="radio"]:checked) {
	background: var(--accent) !important;
	color: #ffffff !important;
	border-color: var(--accent) !important;
	box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2) !important;
}

div[role="radiogroup"] label:has(input[type="radio"]:checked) * {
	color: #ffffff !important;
}

/* Hide Streamlit radio button marker/circle */
div[role="radiogroup"] label [data-testid="stMarker"],
div[role="radiogroup"] label div[role="presentation"],
div[role="radiogroup"] label div:first-child:not([data-testid="stMarkdownContainer"]) {
	display: none !important;
}

div[role="radiogroup"] label div[data-testid="stMarkdownContainer"] {
	padding: 0 !important;
	margin: 0 !important;
}
</style>
"""


def render_dashboard_hero(date_label: str, mode_label: str, total_articles: int, hot_topics: int) -> str:
	return f"""
	<div class="dashboard-hero">
		<div class="dashboard-brand">
			<div class="dashboard-kicker">Hệ Thống Phân Tích Tin Tức AI · Live Dashboard</div>
			<h1 class="dashboard-title">VnNew<span style="color: var(--accent);">AI</span></h1>
			<p class="dashboard-subtitle">Giao diện tòa soạn thông minh giúp phân loại Clickbait, theo dõi cụm chủ đề nóng và phân tích nội dung báo chí Việt Nam.</p>
		</div>
		<div class="dashboard-hero-grid">
			<div class="hero-panel">
				<div class="hero-panel-title">Phiên Làm Việc Hiện Tại</div>
				<p class="hero-panel-copy">Chế độ xem "{html.escape(mode_label)}" đang hoạt động với giao diện tinh gọn, tập trung hiển thị trực quan thông tin.</p>
				<div class="hero-panel-grid">
					<div class="micro-card">
						<div class="micro-card-label">Hôm nay</div>
						<div class="micro-card-value">{html.escape(date_label)}</div>
						<div class="micro-card-note">Dữ liệu được cập nhật trong phiên hiện hành.</div>
					</div>
					<div class="micro-card">
						<div class="micro-card-label">Phạm vi dữ liệu</div>
						<div class="micro-card-value">Thời gian thực</div>
						<div class="micro-card-note">Kết nối trực tiếp với cơ sở dữ liệu bài viết mới nhất.</div>
					</div>
					<div class="micro-card">
						<div class="micro-card-label">Chủ đề nóng</div>
						<div class="micro-card-value">Phát hiện tự động</div>
						<div class="micro-card-note">Cập nhật nhanh các cụm tin tức đang được quan tâm.</div>
					</div>
					<div class="micro-card">
						<div class="micro-card-label">Trải nghiệm</div>
						<div class="micro-card-value">Giao diện Sáng</div>
						<div class="micro-card-note">Tối ưu độ tương phản, sạch sẽ và hiện đại.</div>
					</div>
				</div>
			</div>
			<div class="hero-panel">
				<div class="hero-panel-title">Chế độ đọc tin</div>
				<p class="hero-panel-copy">Sử dụng thanh bộ lọc và bảng điều khiển bên dưới để lọc tin tức hoặc chủ đề nóng mà không lo mất ngữ cảnh.</p>
				<div class="panel-stack" style="margin-top: 18px;">
					<div class="micro-card">
						<div class="micro-card-label">Chế độ hiện tại</div>
						<div class="micro-card-value">{html.escape(mode_label)}</div>
					</div>
					<div class="micro-card">
						<div class="micro-card-label">Giao diện chính</div>
						<div class="micro-card-value">Newsroom Light</div>
					</div>
				</div>
			</div>
		</div>
	</div>
	"""


def render_article_card_html(title: str, summary: str, source: str, category: str, badge_html: str, article_id: str | int | None) -> str:
	article_ref = html.escape(str(article_id or ""))
	return f"""
	<a href="?article_id={article_ref}" target="_self" style="text-decoration: none; color: inherit; display: block;">
		<div class="article-card" data-article-id="{article_ref}">
			<div class="article-card-title">{html.escape(title)}</div>
			<div class="article-card-meta"><span>{html.escape(source)}</span><span>{html.escape(category)}</span></div>
			<div class="article-card-summary">{html.escape(summary)}</div>
			<div style="margin-top: 12px;">{badge_html}</div>
		</div>
	</a>
	"""


def render_topic_card_html(title: str, summary: str, topic_meta: str) -> str:
	return f"""
	<div class="topic-card">
		<div class="topic-card-title">{html.escape(title)}</div>
		<div class="topic-card-meta">{html.escape(topic_meta)}</div>
		<div class="topic-card-summary">{html.escape(summary)}</div>
	</div>
	"""
