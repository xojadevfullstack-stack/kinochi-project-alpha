import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

transcript_path = r'C:\Users\Администратор\.gemini\antigravity\brain\3d3438cd-5de8-40ae-99a7-07b6ccd96a37\.system_generated\logs\transcript.jsonl'
with open(transcript_path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i in [1124, 1165]:
            data = json.loads(line)
            print(f"=== LINE {i} ===")
            print(data.get('content'))

