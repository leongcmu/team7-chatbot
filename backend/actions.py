"""Deterministic conversion policy, separate from LLM-generated prose."""
import re
from .knowledge_base import commercial
from .guardrails import approved_action_url

COURSE_WORDS={'course','courses','class','classes','ielts','toefl','curriculum','lesson','lessons','study','practice'}
PURCHASE_WORDS={'subscribe','subscription','premium','pricing','price','cost','buy','purchase','upgrade','paid'}
APP_WORDS={'app','download','install','iphone','android','ios'}

def tokens(text: str) -> set[str]:
    return set(re.findall(r'[a-z]+',text.lower()))

def select_actions(message: str, *, premium_feature_verified: bool=False) -> list[dict]:
    words=tokens(message)
    cfg=commercial(); actions=[]
    # The client requires both app-store links on every course-related question.
    if words & (COURSE_WORDS|APP_WORDS):
        actions += [{'type':'download_ios','label':'Download for iPhone','url':cfg['ios_url']},
                    {'type':'download_android','label':'Get it on Google Play','url':cfg['android_url']}]
    if words & PURCHASE_WORDS or premium_feature_verified:
        actions.append({'type':'subscribe_website','label':'View website subscriptions','url':cfg['shop_url']})
    return [a for a in actions if approved_action_url(a['url'],a['type'])]
