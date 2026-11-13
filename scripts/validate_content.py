"""Run before publishing edits to curated Eduling data."""
import json
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]
for filename in ['faqs.json','courses.json','blog_posts.json']:
    items=json.loads((ROOT/'data'/filename).read_text())
    seen=set()
    for item in items:
        assert item['id'] not in seen, f'Duplicate ID: {item["id"]}'
        seen.add(item['id'])
        url=item.get('url') or item.get('source_url')
        assert url and urlparse(url).scheme=='https', f'Invalid URL: {item["id"]}'
        assert item.get('status') in {'approved','pending_client_verification','approved_with_note'},item['id']
    print(f'{filename}: {len(items)} records validated')
