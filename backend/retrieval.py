"""Semantic retrieval with a lexical fallback and availability safeguards."""
import re
from difflib import SequenceMatcher
from typing import Literal
from .embeddings import embedding_search
from .knowledge_base import approved

TOKEN_ALIASES = {
    'classes': 'class',
    'courses': 'course',
    'lessons': 'lesson',
    'offered': 'offer',
    'offers': 'offer',
    'provides': 'provide',
    'prep': 'preparation',
}
TOPIC_WEIGHTS = {
    'ielts': 3.0,
    'toefl': 3.0,
    'pronunciation': 2.5,
    'vocabulary': 2.5,
}
SEARCH_GENERIC_WORDS={
    'a','about','an','and','are','can','do','does','eduling','for','how','i','in',
    'is','it','me','of','on','or','please','tell','the','to','what','when','where',
    'whether','which','who','why','with','you','your',
}
AVAILABILITY_WORDS={'offer','provide','available','availability','have','has','practice'}
COURSE_GENERIC_WORDS={
    'a','an','and','are','can','course','do','does','eduling','for','i','in','is','it',
    'language','languages','me','of','offer','or','other','practice','program','provide',
    'the','to','we','what','whether','with','you','your','available','availability','have','has',
    'preparation','test',
}
CourseAvailability=Literal['verified_available','verified_unavailable','unknown']

def normalize(text: str) -> str:
    tokens=re.findall(r"[a-z0-9]+",text.lower())
    return ' '.join(TOKEN_ALIASES.get(token,token) for token in tokens)

def _weighted_overlap(query_tokens: set[str], candidate_tokens: set[str]) -> float:
    """Return weighted Jaccard overlap, emphasizing distinctive learning topics."""
    union=query_tokens | candidate_tokens
    if not union:
        return 0.0
    intersection=query_tokens & candidate_tokens
    weight=lambda token: TOPIC_WEIGHTS.get(token,1.0)
    return sum(weight(token) for token in intersection) / sum(weight(token) for token in union)

def similarity(query: str, candidate: str) -> float:
    # Blend token overlap with fuzzy similarity. Scores are heuristic, not probabilities.
    q, c = normalize(query), normalize(candidate)
    if not q or not c: return 0.0
    qs, cs = set(q.split()), set(c.split())
    overlap=_weighted_overlap(qs,cs)
    fuzzy = SequenceMatcher(None,q,c).ratio()
    return round(0.55*overlap + 0.45*fuzzy, 4)

def is_course_availability_query(query: str) -> bool:
    """Return whether the visitor is asking if a course or practice option exists."""
    words=set(normalize(query).split())
    return bool(words & AVAILABILITY_WORDS and words & ({'course','class','program'} | set(TOPIC_WEIGHTS)))

def _requested_course_terms(query: str) -> set[str]:
    return set(normalize(query).split()) - COURSE_GENERIC_WORDS

def _offering_matches(requested: set[str], offering: str) -> bool:
    offering_terms=set(normalize(offering).split()) - COURSE_GENERIC_WORDS
    return bool(requested) and requested <= offering_terms

def course_availability_state(query: str, evidence: list[dict]) -> CourseAvailability | None:
    """Resolve availability only from explicit structured facts in approved evidence."""
    if not is_course_availability_query(query):
        return None
    requested=_requested_course_terms(query)
    for item in evidence:
        if any(_offering_matches(requested,name) for name in item.get('unavailable_offerings',[])):
            return 'verified_unavailable'
    for item in evidence:
        if any(_offering_matches(requested,name) for name in item.get('available_offerings',[])):
            return 'verified_available'
    return 'unknown'

def filter_course_availability(query: str, matches: list[dict]) -> list[dict]:
    """Remove false positives from specific availability searches."""
    state=course_availability_state(query,matches)
    if state is None:
        return matches
    if state == 'unknown':
        return []
    key='available_offerings' if state == 'verified_available' else 'unavailable_offerings'
    requested=_requested_course_terms(query)
    return [item for item in matches if any(_offering_matches(requested,name) for name in item.get(key,[]))]

def search(query: str, items: list[dict], *, kind: str, limit: int=3,
           min_score: float=0.30, source: str | None=None) -> list[dict]:
    matches=[]
    meaningful_query=set(normalize(query).split())-SEARCH_GENERIC_WORDS
    query_topics=set(normalize(query).split()) & TOPIC_WEIGHTS.keys()
    for item in items:
        if not approved(item): continue
        phrases = [item.get('question',''),item.get('name',''),item.get('title',''),
                   item.get('summary',''),item.get('description',''),item.get('content',''),
                   item.get('answer','')]
        phrases += item.get('alternate_phrasings',[]) + item.get('topics',[])
        candidate_terms=set(normalize(' '.join(
            phrase for phrase in phrases if isinstance(phrase,str)
        )).split())
        if meaningful_query and not meaningful_query & candidate_terms:
            continue
        scored_phrases=[(similarity(query,p),p) for p in phrases if isinstance(p,str)]
        score,matched_text=max(scored_phrases,default=(0,''),key=lambda pair:pair[0])
        if query_topics:
            candidate_topics=set(normalize(' '.join(p for p in phrases if isinstance(p,str))).split()) & TOPIC_WEIGHTS.keys()
            matched_topics=query_topics & candidate_topics
            if matched_topics:
                coverage=len(matched_topics) / len(query_topics)
                score=max(score,0.42 + 0.08*coverage)
            else:
                # Common wording must not outrank an exact distinctive topic match.
                score*=0.5
            score=round(score,4)
        if score >= min_score:
            match={'id':item['id'],'kind':kind,'score':score,
                            'title':item.get('title') or item.get('question') or item.get('name'),
                            'content':item.get('answer') or item.get('description') or item.get('summary') or item.get('content',''),
                            'url':item.get('source_url') or item.get('url'),
                            'retrieval_text':matched_text,
                            'source':source or kind,
                            'status':'approved'}
            for field in ('available_offerings','unavailable_offerings'):
                if field in item:
                    match[field]=item[field]
            matches.append(match)
    return sorted(matches,key=lambda x:(-x['score'],x['id']))[:limit]


def semantic_search(query: str, items: list[dict], *, kind: str, limit: int=3,
                    min_score: float | None=None,
                    source: str | None=None) -> list[dict]:
    """Search a collection by embedding similarity and return approved evidence."""
    usable={item['id']:item for item in items if approved(item)}
    hits=embedding_search(
        query,limit=limit,min_score=min_score,allowed_ids=set(usable),
    )
    if hits:
        relative_floor=hits[0].score-0.12
        hits=[hit for hit in hits if hit.score>=relative_floor]
    matches=[]
    for hit in hits:
        item=usable[hit.record_id]
        match={
            'id':item['id'],'kind':kind,'score':hit.score,
            'title':item.get('title') or item.get('question') or item.get('name'),
            'content':item.get('answer') or item.get('description') or item.get('summary') or item.get('content',''),
            'url':item.get('source_url') or item.get('url'),
            'source':source or kind,'status':'approved',
        }
        for field in ('available_offerings','unavailable_offerings'):
            if field in item:
                match[field]=item[field]
        matches.append(match)
    return matches
