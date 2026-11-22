"""Deterministic tests for backend-controlled evidence retrieval."""
from backend.evidence import MAX_CONTEXT_RECORDS, retrieve_evidence
from backend import evidence
from backend.embeddings import EmbeddingHit


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
    assert 'pricing_premium' in ids


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


def test_semantic_ids_are_resolved_only_against_approved_local_records():
    bundle=retrieve_evidence(
        'Do you have IELTS prep?',
        preferred_ids=['made_up_record','tests_ielts_toefl','company_history'],
    )
    assert [item['id'] for item in bundle.records if item.get('kind')!='commercial']==[
        'tests_ielts_toefl',
    ]


def test_ta_everyday_questions_reach_evidence_not_fallback():
    expected={
        'Do you have IELTS prep?':'tests_ielts_toefl',
        'Is there a TOEFL course?':'tests_ielts_toefl',
        'Can I talk to a real person?':'support_contact',
    }
    for question,record_id in expected.items():
        bundle=retrieve_evidence(question)
        assert record_id in {item['id'] for item in bundle.records}
        assert bundle.coverage=='sufficient_evidence'


def test_embedding_hits_are_resolved_to_approved_evidence(monkeypatch):
    monkeypatch.setattr(evidence,'embedding_search',lambda *_args,**_kwargs:[
        EmbeddingHit('tests_ielts_toefl',0.81),
    ])
    bundle=retrieve_evidence('I need help with an English proficiency exam.')
    assert bundle.retrieval_mode=='embedding'
    assert bundle.records[0]['id']=='tests_ielts_toefl'
    assert bundle.records[0]['score']==0.81
