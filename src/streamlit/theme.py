from __future__ import annotations

import html


def premium_dashboard_styles() -> str:
	return """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@500;700;800&family=Manrope:wght@400;500;600;700&display=swap');

:root {
	--bg: #070a12;
	--bg2: #0b1220;
	--bg3: #101a2c;
	--panel: rgba(15, 23, 38, 0.92);
	--panel-strong: rgba(18, 28, 47, 0.98);
	--panel-border: rgba(122, 146, 181, 0.22);
	--panel-border-strong: rgba(122, 146, 181, 0.34);
	--text: #edf3ff;
	--muted: #9cb1cf;
	--muted-strong: #bdd0ea;
	--accent: #39a6ff;
	--accent-strong: #2f8be0;
	--safe: #34d4ad;
	--danger: #ff6f8a;
	--shadow-soft: 0 10px 26px rgba(0, 0, 0, 0.32);
	--shadow-bold: 0 20px 42px rgba(0, 0, 0, 0.45);
	--radius-lg: 18px;
	--radius-md: 14px;
}

* { box-sizing: border-box; }

html, body, .stApp {
	background:
		radial-gradient(circle at 6% -2%, rgba(57, 166, 255, 0.22), transparent 38%),
		radial-gradient(circle at 95% 0%, rgba(98, 76, 255, 0.18), transparent 34%),
		linear-gradient(180deg, var(--bg) 0%, var(--bg2) 52%, var(--bg3) 100%) !important;
	color: var(--text) !important;
	font-family: "Manrope", "Segoe UI", sans-serif;
}

h1, h2, h3, h4 {
	font-family: "Sora", "Manrope", sans-serif;
	color: var(--text) !important;
}

[data-testid="stHeader"] {
	display: none !important;
}

[data-testid="stAppViewContainer"] {
	background: transparent !important;
	overflow: visible !important;
}

.block-container {
	max-width: 1600px !important;
	padding-top: 1.25rem !important;
	padding-left: clamp(1rem, 2.2vw, 2.2rem) !important;
	padding-right: clamp(1rem, 2.2vw, 2.2rem) !important;
	padding-bottom: 2.4rem !important;
}

a { color: var(--accent); text-decoration: none; font-weight: 700; }
a:hover { color: #78c6ff; text-decoration: underline; }

hr { border-color: rgba(122, 146, 181, 0.28) !important; }

.dashboard-title {
	margin: 0;
	font-size: clamp(2.1rem, 2.8vw, 3.2rem);
	line-height: 1.05;
	letter-spacing: -0.02em;
	font-weight: 800;
}

.dashboard-subtitle {
	max-width: 920px;
	margin: 0;
	color: var(--muted-strong) !important;
	font-size: 1rem;
	line-height: 1.68;
}

.section-title {
	margin: 28px 0 14px;
	font-size: 1.7rem;
	font-weight: 800;
	letter-spacing: -0.01em;
	text-transform: uppercase;
}

.section-title::after {
	content: "";
	display: block;
	width: 96px;
	height: 4px;
	margin-top: 10px;
	border-radius: 999px;
	background: linear-gradient(90deg, #39a6ff, #5c7dff);
}

.article-card,
.topic-card,
.detail-card,
.article-detail {
	position: relative;
	overflow: hidden;
	padding: 18px;
	border-radius: var(--radius-md);
	background: linear-gradient(165deg, rgba(20, 31, 53, 0.96), rgba(14, 21, 36, 0.95));
	border: 1px solid var(--panel-border);
	box-shadow: var(--shadow-soft);
	transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
}

.article-card::before,
.topic-card::before,
.detail-card::before {
	content: "";
	position: absolute;
	inset: 0 0 auto 0;
	height: 3px;
	background: linear-gradient(90deg, #39a6ff, #5c7dff);
	opacity: 0.8;
}

.article-card:hover,
.topic-card:hover,
.detail-card:hover {
	transform: translateY(-2px);
	border-color: var(--panel-border-strong);
	box-shadow: var(--shadow-bold);
}

.article-card-title,
.topic-card-title {
	margin: 0;
	color: var(--text) !important;
	font-size: 1rem;
	font-weight: 700;
	line-height: 1.44;
}

.article-card-meta,
.topic-card-meta,
.detail-meta,
.article-detail-meta {
	display: flex;
	flex-wrap: wrap;
	gap: 6px 12px;
	margin-top: 8px;
	color: var(--muted) !important;
	font-size: 0.68rem;
	font-weight: 700;
	text-transform: uppercase;
	letter-spacing: 0.07em;
}

.article-card-summary,
.topic-card-summary {
	margin-top: 9px;
	color: var(--muted-strong) !important;
	font-size: 0.89rem;
	line-height: 1.58;
}

.article-detail {
	border-radius: var(--radius-lg);
	padding: 24px;
	background: linear-gradient(170deg, rgba(20, 31, 53, 0.98), rgba(13, 20, 35, 0.98));
	box-shadow: var(--shadow-bold);
}

.article-detail-body {
	margin-top: 14px;
	color: var(--text) !important;
	font-size: 0.97rem;
	line-height: 1.8;
	white-space: pre-wrap;
}

.article-detail-url { margin-top: 16px; color: var(--muted-strong); font-weight: 700; }

.featured-badge {
	display: inline-flex;
	align-items: center;
	gap: 6px;
	padding: 4px 11px;
	border-radius: 999px;
	font-size: 0.67rem;
	font-weight: 700;
	letter-spacing: 0.03em;
	text-transform: uppercase;
}

.badge-clickbait {
	background: rgba(255, 111, 138, 0.15);
	border: 1px solid rgba(255, 111, 138, 0.35);
	color: var(--danger);
}

.badge-safe {
	background: rgba(52, 212, 173, 0.14);
	border: 1px solid rgba(52, 212, 173, 0.34);
	color: var(--safe);
}

.badge-unlabeled {
	background: rgba(156, 177, 207, 0.16);
	border: 1px solid rgba(156, 177, 207, 0.28);
	color: var(--muted-strong);
}

.stMetric {
	background: linear-gradient(165deg, rgba(20, 31, 53, 0.96), rgba(14, 21, 36, 0.95)) !important;
	border: 1px solid var(--panel-border) !important;
	border-radius: var(--radius-md) !important;
	padding: 14px 16px !important;
	box-shadow: var(--shadow-soft) !important;
}

[data-testid="stMetricLabel"] {
	font-weight: 700 !important;
	color: var(--muted-strong) !important;
}

[data-testid="stMetricValue"] {
	color: var(--text) !important;
	font-family: "Sora", "Manrope", sans-serif !important;
	font-weight: 800 !important;
	font-size: 1.9rem !important;
}

.stButton button {
	border: 1px solid transparent !important;
	border-radius: 999px !important;
	background: linear-gradient(120deg, #2f8be0 0%, #5c7dff 100%) !important;
	color: #ffffff !important;
	font-family: "Sora", "Manrope", sans-serif !important;
	font-weight: 700 !important;
	box-shadow: 0 12px 22px rgba(31, 101, 181, 0.36) !important;
	transition: transform 150ms ease, box-shadow 150ms ease, filter 150ms ease !important;
}

.stButton button:hover {
	transform: translateY(-1px) !important;
	filter: brightness(1.06) !important;
	box-shadow: 0 16px 28px rgba(31, 101, 181, 0.45) !important;
}

div[role="radiogroup"] {
	display: flex !important;
	flex-wrap: wrap !important;
	flex-direction: row !important;
	justify-content: flex-end !important;
	gap: 10px !important;
	padding: 4px 0 8px !important;
}

div[role="radiogroup"] label {
	border-radius: 999px !important;
	border: 1px solid var(--panel-border) !important;
	background: rgba(17, 27, 44, 0.94) !important;
	padding: 9px 18px !important;
	font-family: "Sora", "Manrope", sans-serif !important;
	font-size: 0.88rem !important;
	font-weight: 700 !important;
	color: var(--muted-strong) !important;
	box-shadow: 0 8px 14px rgba(0, 0, 0, 0.24) !important;
	transition: all 160ms ease !important;
}

div[role="radiogroup"] label:hover {
	border-color: rgba(92, 125, 255, 0.65) !important;
	color: #eaf2ff !important;
}

div[role="radiogroup"] label:hover * { color: #eaf2ff !important; }

div[role="radiogroup"] label:has(input[type="radio"]:checked) {
	background: linear-gradient(110deg, #2f8be0, #5c7dff) !important;
	border-color: transparent !important;
	color: #ffffff !important;
	box-shadow: 0 10px 18px rgba(39, 94, 179, 0.42) !important;
}

div[role="radiogroup"] label:has(input[type="radio"]:checked) * { color: #ffffff !important; }

div[role="radiogroup"] label [data-testid="stMarker"],
div[role="radiogroup"] label div[role="presentation"],
div[role="radiogroup"] label div:first-child:not([data-testid="stMarkdownContainer"]) {
	display: none !important;
}

div[role="radiogroup"] label div[data-testid="stMarkdownContainer"] { padding: 0 !important; margin: 0 !important; }

[data-baseweb="select"] > div,
[data-baseweb="input"] > div,
input {
	border-radius: 12px !important;
	border-color: var(--panel-border) !important;
	background: rgba(17, 27, 44, 0.9) !important;
	color: var(--text) !important;
}

[data-baseweb="select"] > div:hover,
[data-baseweb="input"] > div:hover { border-color: rgba(92, 125, 255, 0.7) !important; }

[data-baseweb="select"] > div:focus-within,
[data-baseweb="input"] > div:focus-within {
	border-color: #5c7dff !important;
	box-shadow: 0 0 0 3px rgba(92, 125, 255, 0.22) !important;
}

[data-testid="stAlert"] {
	border-radius: 12px !important;
	border: 1px solid rgba(120, 164, 214, 0.34) !important;
	background: rgba(26, 44, 70, 0.9) !important;
	color: #d8e8ff !important;
}

[data-testid="stSidebar"],
[data-testid="stSidebarCollapseButton"] {
	display: none !important;
}

@media (max-width: 1000px) {
	.dashboard-title { font-size: clamp(1.8rem, 7.2vw, 2.4rem); }
	.section-title { font-size: 1.28rem; }
	div[role="radiogroup"] { justify-content: flex-start !important; }
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
						<div class="micro-card-value">Newsroom Dark</div>
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

