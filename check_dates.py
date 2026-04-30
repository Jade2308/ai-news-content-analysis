import sqlite3

conn = sqlite3.connect('news.db')
cur = conn.cursor()

# Check thời gian bài viết
result = cur.execute("""
SELECT 
    MIN(crawled_at) as oldest,
    MAX(crawled_at) as newest,
    datetime('now') as now
FROM articles
LIMIT 1
""").fetchall()
print("Date check:", result)

# Check a few articles
print("\nLast 5 articles crawled_at:")
results = cur.execute("SELECT crawled_at FROM articles ORDER BY crawled_at DESC LIMIT 5").fetchall()
for r in results:
    print(r)

conn.close()

