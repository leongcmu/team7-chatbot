"""Backend-controlled semantic evidence selection before agent generation."""
import json
import logging
from dataclasses import dataclass
from typing import Literal

from .actions import select_actions
from .embeddings import EmbeddingUnavailable, embedding_search
from .knowledge_base import approved, commercial, records
from .retrieval import course_availability_state, normalize, search

EvidenceCoverage=Literal['no_evidence','partial_evidence','sufficient_evidence']
RetrievalMode=Literal['embedding','lexical_fallback','preferred_ids']
MAX_CONTEXT_RECORDS=6
MAX_CONTENT_CHARS=500

GENERIC_QUERY_WORDS={
    'a','about','an','and','are','can','course','do','does','eduling','for','how','i',
    'in','is','it','me','of','offer','on','or','please','show','tell','the','to','what',
    'when','where','whether','which','who','why','with','you','your',
}
BLOG_WORDS={'article','articles','blog','blogs','news','post','posts'}
PRICE_COMPARISON_WORDS={'cheaper','lower','less','saving','savings','versus','vs'}
logger=logging.getLogger(__name__)


@dataclass(frozen=True)
class EvidenceBundle:
    records: tuple[dict,...]
    coverage: EvidenceCoverage
    retrieval_mode: RetrievalMode='embedding'

    def context(self) -> str:
        """Return bounded approved JSON for the model's structured input."""
        safe_records=[]
        for item in self.records[:MAX_CONTEXT_RECORDS]:
            safe={
                'id':item.get('id'),
                'kind':item.get('kind'),
                'source':item.get('source'),
                'content':str(item.get('content',''))[:MAX_CONTENT_CHARS],
            }
            for field in ('available_offerings','unavailable_offerings',
                          'website_price_advantage_verified'):
                if field in item:
                    safe[field]=item[field]
            safe_records.append(safe)
        payload={'coverage':self.coverage,'records':safe_records}
        return 'BACKEND_APPROVED_EVIDENCE\n'+json.dumps(payload,ensure_ascii=False,separators=(',',':'))

    def generation_input(self, question: str) -> str:
        """Combine a JSON-escaped question and evidence into one model turn."""
        return 'VISITOR_QUESTION\n'+json.dumps(question,ensure_ascii=False)+'\n'+self.context()


def _meaningful_terms(question: str) -> set[str]:
    return set(normalize(question).split()) - GENERIC_QUERY_WORDS


def _specificity(question_terms: set[str], item: dict) -> float:
    if not question_terms:
        return 1.0
    text=' '.join(str(item.get(field,'')) for field in ('title','content','retrieval_text'))
    item_terms=set(normalize(text).split())
    return len(question_terms & item_terms) / len(question_terms)


def _select_specific(question: str, candidates: list[dict]) -> list[dict]:
    """Prefer direct term coverage so generic fuzzy matches cannot dominate."""
    terms=_meaningful_terms(question)
    if not terms:
        best=max((item.get('score',0) for item in candidates),default=0.0)
        return [item for item in candidates if item.get('score',0)>=best*0.75]
    scored=[(_specificity(terms,item),item) for item in candidates]
    best=max((score for score,_ in scored),default=0.0)
    if best == 0:
        return []
    floor=max(0.5,best*0.75)
    selected=[item for score,item in scored if score>=floor]
    return sorted(selected,key=lambda item:(-item.get('score',0),item.get('id','')))


def select_relevant_evidence(question: str, candidates: list[dict]) -> list[dict]:
    """Apply the same question-specific filter to agent-returned evidence."""
    actions={item['type'] for item in select_actions(question)}
    commercial_records=[]
    factual_records=[]
    for item in candidates:
        if item.get('kind')!='commercial':
            factual_records.append(item)
        elif item.get('id')=='commercial_app_downloads' and actions & {'download_ios','download_android'}:
            commercial_records.append(item)
        elif item.get('id')=='commercial_subscription' and 'subscribe_website' in actions:
            commercial_records.append(item)
        elif item.get('id')=='commercial_support':
            commercial_records.append(item)
    return _select_specific(question,factual_records)+commercial_records


def app_evidence(reason: str='course_discovery') -> dict:
    """Return the canonical approved app-download evidence record."""
    cfg=commercial()
    return {
        'id':'commercial_app_downloads','kind':'commercial','source':'commercial.json',
        'score':1.0,'status':'approved','reason':reason,
        'title':'Official Eduling app downloads',
        'content':'Official iOS and Android app download actions are available. Courses are accessed through the app.',
        'ios_url':cfg['ios_url'],'android_url':cfg['android_url'],
    }


def subscription_evidence(reason: str='purchase_interest') -> dict:
    """Return the canonical approved subscription evidence record."""
    cfg=commercial()
    return {
        'id':'commercial_subscription','kind':'commercial','source':'commercial.json',
        'score':1.0,'status':'approved','reason':reason,
        'title':'Eduling website subscriptions',
        'content':(
            'Website subscriptions can be viewed using the verified subscription action. '
            'Exact current prices and any website-versus-app price advantage are not verified.'
        ),
        'shop_url':cfg['shop_url'],
        'website_price_advantage_verified':bool(cfg.get('price_comparison_approved')),
        'premium_only_features':cfg.get('premium_only_features',[]),
    }


def support_evidence(reason: str='unresolved_question') -> dict:
    """Return the canonical approved support-route evidence record."""
    return {
        'id':'commercial_support','kind':'commercial','source':'commercial.json',
        'score':1.0,'status':'approved','reason':reason,
        'title':'Eduling support route',
        'content':'Visitors can contact Eduling support by email or through the verified contact route.',
        'email':'info@eduling.org','contact_url':'https://www.eduling.ai/contact',
    }


def _lexical_knowledge_records(question: str) -> list[dict]:
    candidates=[]
    candidates+=search(question,records('faqs.json'),kind='faq',limit=4,
                       min_score=0.30,source='faqs.json')
    candidates+=search(question,records('courses.json'),kind='course',limit=3,
                       min_score=0.30,source='courses.json')
    candidates+=search(question,records('blog_posts.json'),kind='blog',limit=2,
                       min_score=0.42,source='blog_posts.json')
    deduplicated={}
    for item in candidates:
        current=deduplicated.get(item['id'])
        if current is None or item['score']>current['score']:
            deduplicated[item['id']]=item
    return _select_specific(question,list(deduplicated.values()))


def _evidence_for_ids(record_ids: list[str], scores: dict[str,float] | None=None) -> list[dict]:
    """Resolve selected IDs against approved local records."""
    wanted=set(record_ids[:MAX_CONTEXT_RECORDS])
    selected=[]
    for filename,kind in (
        ('faqs.json','faq'),('courses.json','course'),('blog_posts.json','blog'),
    ):
        for item in records(filename):
            if item.get('id') not in wanted or not approved(item):
                continue
            match={
                'id':item['id'],'kind':kind,
                'score':(scores or {}).get(item['id'],1.0),
                'title':item.get('title') or item.get('question') or item.get('name'),
                'content':item.get('answer') or item.get('description') or item.get('summary') or item.get('content',''),
                'url':item.get('source_url') or item.get('url'),
                'source':filename,'status':'approved',
            }
            for field in ('available_offerings','unavailable_offerings'):
                if field in item:
                    match[field]=item[field]
            selected.append(match)
    order={record_id:index for index,record_id in enumerate(record_ids)}
    return sorted(selected,key=lambda item:order.get(item['id'],len(order)))


def _commercial_records(question: str) -> list[dict]:
    actions=select_actions(question)
    action_types={action['type'] for action in actions}
    selected=[]
    if action_types & {'download_ios','download_android'}:
        selected.append(app_evidence('deterministic_course_action'))
    if 'subscribe_website' in action_types:
        selected.append(subscription_evidence('deterministic_purchase_action'))
    return selected


def retrieve_evidence(question: str, *, preferred_ids: list[str] | None=None) -> EvidenceBundle:
    """Retrieve bounded approved evidence and estimate whether it fully answers the question."""
    if preferred_ids is not None:
        knowledge=_evidence_for_ids(preferred_ids)
        retrieval_mode='preferred_ids'
    else:
        try:
            hits=embedding_search(question,limit=1)
            knowledge=_evidence_for_ids(
                [hit.record_id for hit in hits],
                {hit.record_id:hit.score for hit in hits},
            )
            retrieval_mode='embedding'
        except EmbeddingUnavailable as exc:
            logger.warning('embedding_retrieval_unavailable type=%s',type(exc).__name__)
            knowledge=_lexical_knowledge_records(question)
            retrieval_mode='lexical_fallback'
    commercial_records=_commercial_records(question)
    knowledge_limit=max(0,MAX_CONTEXT_RECORDS-len(commercial_records))
    combined=knowledge[:knowledge_limit]+commercial_records
    words=set(normalize(question).split())
    blog_requested=bool(words & BLOG_WORDS)
    availability=course_availability_state(question,knowledge)
    asks_price_comparison=bool(words & PRICE_COMPARISON_WORDS and words & {'price','prices','pricing','cost','website','app'})

    if availability == 'unknown':
        coverage='partial_evidence' if commercial_records else 'no_evidence'
    elif blog_requested and not any(item.get('kind')=='blog' for item in knowledge):
        coverage='no_evidence'
    elif asks_price_comparison and not commercial().get('price_comparison_approved'):
        coverage='partial_evidence'
    elif combined:
        coverage='sufficient_evidence'
    else:
        coverage='no_evidence'
    return EvidenceBundle(tuple(combined),coverage,retrieval_mode)


def merge_evidence(*groups: list[dict] | tuple[dict,...]) -> list[dict]:
    """Deduplicate pre-retrieved and agent-tool evidence by stable record ID."""
    merged={}
    for group in groups:
        for item in group:
            if isinstance(item,dict) and item.get('status')=='approved' and item.get('id'):
                merged[item['id']]=item
    return list(merged.values())
