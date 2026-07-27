import sqlite3

db = sqlite3.connect(r'C:\Users\Aziz\.gemini\antigravity\conversations\f68e40c1-9d71-46f7-a3b5-91dc71a7d854.db')
c = db.cursor()

# Get all table names
c.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = c.fetchall()
print("Tables:", tables)

# We expect an events or messages table
for t in tables:
    try:
        c.execute(f"SELECT * FROM {t[0]} LIMIT 1")
        columns = [description[0] for description in c.description]
        if 'content' in columns:
            c.execute(f"SELECT content FROM {t[0]}")
            rows = c.fetchall()
            longest = max([r[0] for r in rows if r[0] is not None], key=len)
            print(f"Table {t[0]} longest content: {len(longest)}")
            if len(longest) > 10000:
                with open(r'E:\Talk\gemini_full.txt', 'w', encoding='utf-8') as f:
                    f.write(longest)
    except Exception as e:
        print(f"Error on table {t[0]}: {e}")
