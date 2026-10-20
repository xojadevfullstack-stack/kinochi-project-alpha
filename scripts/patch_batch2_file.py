import json
import re

with open("batch2_real_posters.json", "r", encoding="utf-8") as f:
    real_posters = json.load(f)

real_posters["479144"] = "https://image.tmdb.org/t/p/w500/9ySkFLATDGH6ML0AA87QldiGQyB.jpg"
real_posters["469469"] = "https://image.tmdb.org/t/p/w500/9ySkFLATDGH6ML0AA87QldiGQyB.jpg"

file_path = "scripts/migrate_batch2_movies_individual_topics.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

count = 0
for tid_str, real_url in real_posters.items():
    tid = int(tid_str)
    # Match lines with "tmdb_id": <tid>, ... "poster_url": "..."
    # or "poster_url": "...", ... "tmdb_id": <tid>
    pattern = rf'("tmdb_id":\s*{tid},\s*"poster_url":\s*")[^"]+(")'
    new_content, n = re.subn(pattern, rf'\g<1>{real_url}\g<2>', content)
    if n > 0:
        content = new_content
        count += n

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Updated {count} poster URLs in {file_path}")
