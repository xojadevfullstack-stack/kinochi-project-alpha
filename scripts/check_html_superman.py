import urllib.request
import re

req = urllib.request.Request("http://localhost:3000/movies")
html = urllib.request.urlopen(req).read().decode("utf-8")

match = re.search(r'<img[^>]*alt="Supermen \(2025\)"[^>]*>', html)
if match:
    print("Found img tag:")
    print(match.group(0))
else:
    # Look for any img near Supermen (2025)
    idx = html.find("Supermen (2025)")
    print("Near Supermen:")
    print(html[idx-300:idx+300])
