"""Six client-specific, LLM-callable tools with agent-readable docstrings.

All factual tools return JSON-friendly records from approved Eduling content.
Tools are read-only: no purchases, accounts, or external actions are performed.
"""
from langchain_core.tools import tool
from .knowledge_base import records
from .retrieval import filter_course_availability, semantic_search
from .evidence import app_evidence, subscription_evidence, support_evidence

@tool
def search_approved_faq(query: str) -> list[dict]:
    """Search verified Eduling FAQs for product, educator, or support facts.

    Use when the visitor asks how Eduling works or what features are available.
    Return ranked evidence; if empty, do not invent an answer.
    """
    return semantic_search(query,records('faqs.json'),kind='faq',source='faqs.json')

@tool
def search_course_catalog(query: str) -> list[dict]:
    """Search approved course-category information for a learning goal.

    Use for IELTS, TOEFL, pronunciation, vocabulary, course availability, and
    differences between courses. It searches approved course facts across the
    curated FAQ and catalog collections.
    Structured offering fields prove availability or unavailability. A missing
    result means availability is unknown, never that a course does not exist.
    """
    faq_courses=[item for item in records('faqs.json') if item.get('category')=='courses']
    matches=semantic_search(query,faq_courses,kind='course',limit=3,source='faqs.json')
    matches+=semantic_search(query,records('courses.json'),kind='course',limit=3,source='courses.json')
    ranked=sorted(matches,key=lambda item:(-item['score'],item['id']))
    return filter_course_availability(query,ranked)[:3]

@tool
def search_blog_posts(query: str) -> list[dict]:
    """Find up to two verified Eduling articles related to a visitor's learning goal.

    Use when educational reading would help or the visitor asks for articles.
    Return an empty list when no sufficiently relevant article is approved.
    Do not invent article titles or URLs.
    """
    return semantic_search(query,records('blog_posts.json'),kind='blog',limit=2,
                           min_score=0.42,source='blog_posts.json')

@tool
def get_app_download_info(reason: str='course_discovery') -> dict:
    """Retrieve official iOS and Android Eduling download destinations.

    Use when visitors ask about courses, practice, installing, or getting started.
    Courses are accessed through the app; never claim an unverified course exists.
    """
    return app_evidence(reason)

@tool
def get_subscription_info(reason: str='purchase_interest') -> dict:
    """Retrieve approved website subscription destination and pricing-claim status.

    Use for premium, pricing, upgrade or purchase interest, or a confirmed
    premium-only feature. Never invent prices, savings, or premium entitlements.
    """
    return subscription_evidence(reason)

@tool
def get_support_route(reason: str='unresolved_question') -> dict:
    """Provide Eduling's approved support route when the question is unresolved.

    Use for account-specific requests, uncertain availability, or a human handoff.
    Never imply the chatbot can access private accounts or create tickets.
    """
    return support_evidence(reason)

TOOLS=[search_approved_faq,search_course_catalog,search_blog_posts,
       get_app_download_info,get_subscription_info,get_support_route]
