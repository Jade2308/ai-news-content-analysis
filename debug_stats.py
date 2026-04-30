import sqlite3

# Test query trực tiếp
conn = sqlite3.connect('news.db')
cur = conn.cursor()

# Test 1: Query đơn giản không có WHERE
query1 = """
SELECT
    COUNT(*) AS total_articles,
    SUM(CASE WHEN predicted_label = 'clickbait' THEN 1 ELSE 0 END) AS clickbait_count,
    SUM(CASE WHEN predicted_label = 'non-clickbait' THEN 1 ELSE 0 END) AS non_clickbait_count,
    SUM(CASE WHEN predicted_label IS NOT NULL THEN 1 ELSE 0 END) AS labeled_count,
    AVG(prediction_score) AS avg_score
FROM articles
"""
result1 = cur.execute(query1).fetchall()
print("Test 1 (no WHERE):", result1)

# Test 2: Query với WHERE time clause
query2 = """
SELECT
    COUNT(*) AS total_articles,
    SUM(CASE WHEN predicted_label = 'clickbait' THEN 1 ELSE 0 END) AS clickbait_count,
    SUM(CASE WHEN predicted_label = 'non-clickbait' THEN 1 ELSE 0 END) AS non_clickbait_count,
    SUM(CASE WHEN predicted_label IS NOT NULL THEN 1 ELSE 0 END) AS labeled_count,
    AVG(prediction_score) AS avg_score
FROM articles
WHERE crawled_at >= datetime('now', '-' || ? || ' hours')
"""
result2 = cur.execute(query2, (24,)).fetchall()
print("Test 2 (with time WHERE):", result2)

conn.close()
print("Debug complete!")

