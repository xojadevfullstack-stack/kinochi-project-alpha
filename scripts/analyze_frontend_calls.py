import os
import re
import sys

sys.path.insert(0, os.path.abspath("backend"))
import app.main as m

def normalize_template_string(s):
    # Replace ${...} with {param}
    return re.sub(r'\$\{[^}]+\}', '{param}', s)

pattern = re.compile(r'fetchApi\([\"\'`](/[^\"\'`\?]+)[\"\'`]')
method_pattern = re.compile(r'method:\s*[\"\'`](GET|POST|PUT|PATCH|DELETE)[\"\'`]', re.I)

calls = []
for base in ['website', 'admin-panel']:
    for root, dirs, files in os.walk(base):
        if any(x in root for x in ['node_modules', '.next', '.git']):
            continue
        for f in files:
            if f.endswith(('.ts', '.tsx')):
                p = os.path.join(root, f)
                with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                    content = fp.read()
                    for match in pattern.finditer(content):
                        raw_path = match.group(1).split('?')[0]
                        norm_path = normalize_template_string(raw_path)
                        start = max(0, match.start() - 50)
                        end = min(len(content), match.end() + 150)
                        window = content[start:end]
                        mm = method_pattern.search(window)
                        meth = mm.group(1).upper() if mm else 'GET'
                        calls.append({'base': base, 'raw_path': raw_path, 'norm_path': norm_path, 'method': meth, 'file': os.path.relpath(p, '.')})

unique_calls = {}
for c in calls:
    key = (c['method'], c['norm_path'])
    unique_calls.setdefault(key, []).append(c['file'])

print(f"Total fetchApi call sites: {len(calls)}")
print(f"Unique (Method, Normalized Path): {len(unique_calls)}")

# Extract all backend routes with their methods
backend_routes = []
for r in m.app.routes:
    if hasattr(r, 'original_router'):
        prefix = getattr(r.include_context, 'prefix', '')
        for sub in r.original_router.routes:
            sub_path = prefix + getattr(sub, 'path', '')
            sub_methods = getattr(sub, 'methods', set())
            backend_routes.append({'path': sub_path, 'methods': sub_methods})
    else:
        r_path = getattr(r, 'path', '')
        r_methods = getattr(r, 'methods', set())
        backend_routes.append({'path': r_path, 'methods': r_methods})

print(f"Total backend routes: {len(backend_routes)}")

matched = []
unmatched = []

for (meth, norm_path), files in sorted(unique_calls.items()):
    full_v1 = f"/api/v1{norm_path}"
    path_regex = "^" + re.sub(r'\{[^}]+\}', r'[^/]+', norm_path).rstrip('/') + "/?$"
    v1_regex = "^" + re.sub(r'\{[^}]+\}', r'[^/]+', full_v1).rstrip('/') + "/?$"
    
    found = False
    for br in backend_routes:
        b_path = br['path']
        b_methods = br['methods']
        # Check regex match
        if re.match(v1_regex, b_path) or re.match(path_regex, b_path):
            if not b_methods or meth in b_methods:
                found = True
                matched.append((meth, norm_path, b_path))
                break
    if not found:
        unmatched.append((meth, norm_path, files))

print(f"Matched: {len(matched)} / {len(unique_calls)} ({len(matched)/len(unique_calls)*100:.1f}%)")
if unmatched:
    print(f"REAL UNMATCHED CALLS ({len(unmatched)}):")
    for meth, norm_path, files in unmatched:
        print(f"  [{meth}] {norm_path} in {files[0]}")
