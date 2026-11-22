"""Load client-curated JSON. The backend never scrapes sites during a chat."""
import json
import re
from functools import lru_cache
from urllib.parse import urlparse
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

def approved_records() -> list[dict]:
    """Return every approved public content record from the curated KB."""
    return [
        item for filename in ('faqs.json','courses.json','blog_posts.json')
        for item in records(filename) if approved(item)
    ]

def all_records() -> list[dict]:
    """Return public content records, including review-pending rejection targets."""
    return [
        item for filename in ('faqs.json','courses.json','blog_posts.json')
        for item in records(filename)
    ]

def _strings(value):
    if isinstance(value,str):
        yield value
    elif isinstance(value,dict):
        for nested in value.values():
            yield from _strings(nested)
    elif isinstance(value,list):
        for nested in value:
            yield from _strings(nested)

@lru_cache
def approved_urls() -> frozenset[str]:
    """Build the URL allowlist from approved content and commercial config."""
    sources=[*approved_records(),commercial()]
    urls=set()
    for source in sources:
        for text in _strings(source):
            for match in re.findall(r'https://[^\s<>"\']+',text):
                url=match.rstrip('.,);]')
                if urlparse(url).scheme=='https':
                    urls.add(url)
    return frozenset(urls)

@lru_cache
def approved_prices() -> frozenset[str]:
    """Build the exact price allowlist only from approved public records."""
    return frozenset(
        match
        for item in approved_records()
        for text in _strings(item)
        for match in re.findall(r'\$\s*\d+(?:\.\d{2})?',text)
    )
