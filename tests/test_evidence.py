"""Deterministic tests for backend-controlled evidence retrieval."""
from backend.evidence import MAX_CONTEXT_RECORDS, retrieve_evidence


def test_ielts_pre_retrieval_selects_specific_approved_record():
    bundle=retrieve_evidence('What IELTS speaking courses does Eduling offer?')
    assert bundle.coverage=='sufficient_evidence'
    assert bundle.records[0]['id']=='tests_ielts_toefl'
    assert 'company_what_is_eduling' not in {item['id'] for item in bundle.records}


def test_premium_purchase_pre_retrieval_adds_subscription_evidence_only():
    bundle=retrieve_evidence('How do I buy premium?')
    ids={item['id'] for item in bundle.records}
    assert bundle.coverage=='sufficient_evidence'
    assert 'commercial_subscription' in ids
    assert 'pricing_premium' not in ids


def test_website_price_comparison_is_partial_and_unverified():
    bundle=retrieve_evidence('Is website pricing cheaper than the app?')
    subscription=next(item for item in bundle.records if item['id']=='commercial_subscription')
    assert bundle.coverage=='partial_evidence'
    assert subscription['website_price_advantage_verified'] is False


def test_unsupported_course_has_only_partial_app_evidence():
    bundle=retrieve_evidence('Does Eduling offer an advanced Japanese business course?')
    assert bundle.coverage=='partial_evidence'
    assert [item['id'] for item in bundle.records]==['commercial_app_downloads']


def test_missing_blog_results_are_no_evidence_and_context_is_bounded():
    bundle=retrieve_evidence('Show me blog posts about vocabulary')
    assert bundle.coverage=='no_evidence'
    assert not any(item.get('kind')=='blog' for item in bundle.records)
    assert len(bundle.records)<=MAX_CONTEXT_RECORDS


def test_generic_question_keeps_only_the_direct_company_match():
    bundle=retrieve_evidence('What is Eduling?')
    assert [item['id'] for item in bundle.records]==['company_what_is_eduling']
