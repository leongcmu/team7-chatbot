"""Load client-curated JSON. The backend never scrapes sites during a chat."""
import json
from functools import lru_cache
from .config import ROOT

@lru_cache
def records(filename: str) -> list[dict]:
    allowed = {'faqs.json','courses.json','blog_posts.json'}
    if filename not in allowed:
        raise ValueError('Unknown content collection')
    data = json.loads((ROOT/'data'/filename).read_text(encoding='utf-8'))
    if not isinstance(data,list):
        raise ValueError(f'{filename} must contain a JSON list')
    return data

@lru_cache
def commercial() -> dict:
    return json.loads((ROOT/'data'/'commercial.json').read_text(encoding='utf-8'))

def approved(record: dict) -> bool:
    # Original notebook also used approved_with_note; exclude it until reviewed.
    return record.get('status', record.get('approval_status')) == 'approved'
