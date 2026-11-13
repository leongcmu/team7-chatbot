"""Application-level guards: never rely on voluntary agent tool calls for safety."""
import re
from urllib.parse import urlparse
from .knowledge_base import commercial

PATTERNS=[r'ignore\s+(?:all\s+)?(?:previous\s+|your\s+)?instructions',r'reveal.*system prompt',r'print.*api.*key']

CLAIM_ALIASES={
    'build':'practice','built':'practice','exam':'test','exams':'test',
    'oral':'speaking','prep':'preparation','train':'practice','training':'practice',
    'written':'writing','headsets':'headset','courses':'course','classes':'class',
    'learners':'learner','skills':'skill',
}
PRODUCT_SUBJECTS={
    'eduling','platform','app','application','course','courses','class','classes',
    'learner','learners','student','students','subscription','subscriptions',
}
PRODUCT_CLAIM_VERBS={
    'allow','allows','are','can','feature','features','has','have','help','helps',
    'include','includes','is','let','lets','offer','offers','provide','provides',
    'support','supports','use','uses',
}
UNCERTAINTY_WORDS={'cannot','couldn','couldnt','unknown','uncertain','unverified','verify'}
CLAIM_STOPWORDS={
    'a','an','and','are','as','at','be','both','by','can','does','eduling','for','from',
    'has','have','in','include','includes','is','it','its','of','on','or','offer','offers',
    'provide','provides','support','supports','the','to','use','uses','with','yes',
    'course','class','program','platform','app','application','learner','student',
}

def validate_input(message: str) -> str | None:
    if not message.strip(): return 'empty_message'
    if len(message)>1500: return 'message_too_long'
    if any(re.search(p,message,re.I) for p in PATTERNS): return 'instruction_override'
    return None

def approved_action_url(url: str, action_type: str) -> bool:
    cfg=commercial()
    mapping={'download_ios':'ios_url','download_android':'android_url','subscribe_website':'shop_url'}
    if action_type not in mapping: return False
    return url == cfg.get(mapping[action_type]) and urlparse(url).scheme=='https'

def answer_checks(answer: str) -> list[str]:
    # Narrow lexical checks; cannot establish full natural-language factuality.
    problems=[]
    if re.search(r'\$\s*\d',answer): problems.append('unverified_price')
    if re.search(r'(system prompt is|gemini_api_key)',answer,re.I): problems.append('possible_secret_disclosure')
    # All URLs are rendered separately by the backend; prose must not invent links.
    if re.search(r'https?://',answer): problems.append('url_in_prose')
    return problems

def evidence_checks(answer: str, evidence: list[dict]) -> list[str]:
    """Reject obvious factual claims that are not present in approved evidence.

    This is intentionally conservative and lexical. It supplements rather than
    replaces the model prompt and approval checks.
    """
    if not evidence:
        return ['no_evidence']
    evidence_text=' '.join(
        str(value) for item in evidence for value in (item.get('title',''),item.get('content',''))
    ).lower()
    # Exam acronyms are high-risk course claims and must appear in tool evidence.
    acronyms={token.lower() for token in re.findall(r'\b[A-Z]{2,6}\b',answer)} - {'ai'}
    if any(acronym not in evidence_text for acronym in acronyms):
        return ['unsupported_named_course']

    evidence_terms=_claim_tokens(evidence_text)
    for sentence in re.split(r'(?<=[.!?])\s+',answer):
        raw_tokens=set(re.findall(r'[a-z0-9]+',sentence.lower()))
        if raw_tokens & UNCERTAINTY_WORDS:
            continue
        if not raw_tokens & PRODUCT_SUBJECTS or not raw_tokens & PRODUCT_CLAIM_VERBS:
            continue
        claim_terms=_claim_tokens(sentence)
        supported=claim_terms & evidence_terms
        unsupported=claim_terms - evidence_terms
        # Validate factual product clauses, not stylistic wording across the
        # whole answer. A lone synonym is tolerated; unsupported claim clusters
        # such as "virtual reality tutoring and headsets" are not.
        if claim_terms and (not supported or (len(unsupported)>=2 and len(unsupported)>len(supported))):
            return ['unsupported_product_claim']
    return []

def _claim_tokens(text: str) -> set[str]:
    """Normalize factual vocabulary while preserving product-specific terms."""
    normalized={CLAIM_ALIASES.get(token,token) for token in re.findall(r'[a-z0-9]+',text.lower())}
    normalized={token[:-1] if token.endswith('s') and len(token)>4 else token for token in normalized}
    return normalized - CLAIM_STOPWORDS - PRODUCT_CLAIM_VERBS

def availability_claim_checks(answer: str, state: str | None) -> list[str]:
    """Detect model wording that contradicts structured availability evidence."""
    negative=bool(re.search(
        r"\b(?:do|does|did)\s+not\s+(?:offer|have|provide)|\bnot\s+available|\bno\s+[\w -]+\s+(?:course|class|program)",
        answer,re.I,
    ))
    positive=bool(re.search(r'\b(?:offer|offers|has|have|provides?)\b.*\b(?:course|class|program)\b',answer,re.I))
    if state == 'verified_available' and negative:
        return ['availability_contradiction']
    if state == 'verified_unavailable' and positive and not negative:
        return ['availability_contradiction']
    return []

def commercial_claim_checks(answer: str, evidence: list[dict]) -> list[str]:
    """Reject price comparisons that commercial metadata marks unverified."""
    comparison_unverified=any(
        item.get('id')=='commercial_subscription'
        and item.get('website_price_advantage_verified') is False
        for item in evidence
    )
    claims_advantage=bool(re.search(
        r'\b(?:website|web)\b.{0,60}\b(?:cheaper|lower|less expensive|better price)\b'
        r'|\b(?:cheaper|lower|less expensive)\b.{0,60}\b(?:app|in-app)\b',
        answer,re.I,
    ))
    return ['unverified_price_comparison'] if comparison_unverified and claims_advantage else []
