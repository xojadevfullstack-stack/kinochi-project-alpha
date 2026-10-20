import urllib.request
import re

req = urllib.request.Request("http://localhost:3000/series")
html = urllib.request.urlopen(req).read().decode("utf-8")

for name in ["Kontinental", "Persi Jekson", "Shtamm", "Originals"]:
    match = re.search(rf'<img[^>]*alt="[^"]*{name}[^"]*"[^>]*>', html, re.IGNORECASE)
    if match:
        print(f"Match for {name}:")
        print(match.group(0))
    else:
        print(f"No match for {name}")
