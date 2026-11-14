import os
import re
import json

base_dir = "website"

# 1. Map all guest-accessible pages
pages = []
for root, dirs, files in os.walk(os.path.join(base_dir, "app")):
    for f in files:
        if f.endswith(("page.tsx", "page.js")):
            rel = os.path.relpath(os.path.join(root, f), base_dir)
            pages.append(rel)

print(f"Total pages found: {len(pages)}")

# 2. Extract buttons and onClick handlers across website/app and website/components
components = []
for root, dirs, files in os.walk(base_dir):
    if any(x in root for x in ["node_modules", ".next", ".git", "tests"]):
        continue
    for f in files:
        if f.endswith((".tsx", ".jsx")):
            components.append(os.path.join(root, f))

print(f"Total TSX/JSX components to scan: {len(components)}")

dead_buttons = []
silent_catches = []
fake_successes = []
hardcoded_mocks = []
auth_checks = []
api_calls = []

btn_pattern = re.compile(r'<button\b([^>]*)>(.*?)</button>', re.DOTALL)
onclick_empty_pattern = re.compile(r'onClick=\{\s*(\(\)\s*=>\s*\{\s*\}|\(\)\s*=>\s*undefined|\(\)\s*=>\s*null)\s*\}')
dead_href_pattern = re.compile(r'href=[\"\'`](#|javascript:void\(0\);?)[\"\'`]')
catch_empty_pattern = re.compile(r'catch\s*\([^\)]*\)\s*\{\s*(\/\/[^\n]*\n\s*)?\}')
catch_console_only = re.compile(r'catch\s*\(([^\)]*)\)\s*\{\s*console\.(error|warn|log)\([^)]*\);\s*\}')
fetch_pattern = re.compile(r'fetchApi\([\"\'`]([^\"\'`]+)[\"\'`]')

for c_path in components:
    rel_path = os.path.relpath(c_path, ".")
    try:
        with open(c_path, "r", encoding="utf-8", errors="ignore") as fp:
            content = fp.read()
            lines = content.splitlines()

            # Scan line by line for precise line numbers
            for idx, line in enumerate(lines, 1):
                # Empty or dead onClick
                if onclick_empty_pattern.search(line):
                    dead_buttons.append((rel_path, idx, line.strip(), "Empty onClick handler"))
                if dead_href_pattern.search(line):
                    dead_buttons.append((rel_path, idx, line.strip(), "Dead href anchor"))

                # Empty catch
                if catch_empty_pattern.search(line):
                    silent_catches.append((rel_path, idx, line.strip(), "Completely silent catch block"))
                elif catch_console_only.search(line):
                    silent_catches.append((rel_path, idx, line.strip(), "Console-only swallowed exception (no UI error state)"))

                # Hardcoded mock markers
                if re.search(r'\b(mock|dummy|fake|sampleData|mockData)\b', line, re.I):
                    hardcoded_mocks.append((rel_path, idx, line.strip()))

                # API calls
                m_fetch = fetch_pattern.search(line)
                if m_fetch:
                    api_calls.append((rel_path, idx, m_fetch.group(1)))

                # Auth status checks
                if "status ===" in line or "status !==" in line:
                    auth_checks.append((rel_path, idx, line.strip()))

    except Exception as e:
        print(f"Error reading {c_path}: {e}")

print(f"\n--- SCAN RESULTS ---")
print(f"Dead buttons / empty onClick: {len(dead_buttons)}")
for d in dead_buttons[:10]:
    print(f"  {d[0]}:{d[1]} -> {d[2]} ({d[3]})")

print(f"\nSilent catches / console-only swallows: {len(silent_catches)}")
for s in silent_catches[:10]:
    print(f"  {s[0]}:{s[1]} -> {s[2]} ({s[3]})")

print(f"\nHardcoded mock references in code: {len(hardcoded_mocks)}")
for h in hardcoded_mocks[:10]:
    print(f"  {h[0]}:{h[1]} -> {h[2]}")

print(f"\nAPI calls count: {len(api_calls)}")
print(f"Auth checks count: {len(auth_checks)}")
