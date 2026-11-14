import os
import re
import sys

sys.path.insert(0, os.path.abspath("backend"))

import app.main as m

def extract_routes(app):
    routes = []
    for r in app.routes:
        if hasattr(r, 'path') and not hasattr(r, 'original_router'):
            routes.append(r.path)
        elif hasattr(r, 'original_router'):
            prefix = getattr(r.include_context, 'prefix', '')
            for sub in r.original_router.routes:
                sub_path = getattr(sub, 'path', '')
                routes.append(prefix + sub_path)
    return routes

backend_routes = extract_routes(m.app)
print(f"Total real backend routes: {len(backend_routes)}")

frontend_calls = set()
pattern = re.compile(r'fetchApi\([\"\'\`](\/[^\"\'\`\?\$]+)')

for base in ['website', 'admin-panel']:
    for root, dirs, files in os.walk(base):
        if any(x in root for x in ['node_modules', '.next', '.git']):
            continue
        for f in files:
            if f.endswith(('.ts', '.tsx', '.js')):
                p = os.path.join(root, f)
                try:
                    with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                        for line in fp:
                            m = pattern.search(line)
                            if m:
                                frontend_calls.add((base, m.group(1), os.path.relpath(p, ".")))
                except Exception:
                    pass

print(f"Total unique frontend fetchApi paths called: {len(frontend_calls)}")

missing = []
matched_count = 0
for base, path, src in sorted(frontend_calls):
    full_path_v1 = f"/api/v1{path}"
    direct_path = path
    matched = False
    for br in backend_routes:
        # replace {param} with regex [^/]+
        pattern_re = "^" + re.sub(r'\{[^}]+\}', r'[^/]+', br).rstrip('/') + "/?$"
        if re.match(pattern_re, full_path_v1) or re.match(pattern_re, direct_path):
            matched = True
            break
    if matched:
        matched_count += 1
    else:
        missing.append((base, path, src))

print(f"Matched successfully: {matched_count}")
print(f"MISMATCHED / MISSING ENDPOINTS: {len(missing)}")
for base, path, src in missing:
    print(f"  [{base.upper()}] {path} (in {src})")
