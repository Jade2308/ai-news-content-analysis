import sqlite3

conn = sqlite3.connect('news.db')
cur = conn.cursor()

cur.execute('SELECT COUNT(*) FROM articles')
total = cur.fetchone()[0]
print(f'Total articles: {total}')

cur.execute('SELECT COUNT(*) FROM articles WHERE predicted_label IS NOT NULL')
labeled = cur.fetchone()[0]
print(f'Labeled: {labeled}')

cur.execute('SELECT COUNT(*) FROM articles WHERE predicted_label="clickbait"')
clickbait = cur.fetchone()[0]
print(f'Clickbait: {clickbait}')

if labeled > 0:
    ratio = (clickbait / labeled * 100)
    print(f'Ratio: {ratio:.1f}%')

conn.close()

