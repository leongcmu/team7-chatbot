"""Deterministic agent orchestration tests; no Gemini calls are made."""
import json
import logging
from types import SimpleNamespace

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from backend import agent
from backend.evidence import retrieve_evidence
from backend.tools import search_course_catalog
from backend.tools import get_app_download_info, get_subscription_info


class FakeAgent:
    def __init__(self, messages):
        self.messages=messages

    def invoke(self, payload, config):
        return {'messages':[payload['messages'][0], *self.messages]}


class CapturingAgent(FakeAgent):
    def invoke(self,payload,config):
        self.payload=payload
        return {'messages':[*payload['messages'], *self.messages]}


def _tool_message(records):
    return ToolMessage(
        content=json.dumps(records),
        tool_call_id='call_1',
        name='search_course_catalog',
    )


def test_course_tool_makes_approved_ielts_record_available_to_agent():
    results=search_course_catalog.invoke({'query':'What IELTS speaking courses does Eduling offer?'})
    assert any(
        result['id']=='tests_ielts_toefl'
        and result['status']=='approved'
        and result['source']=='faqs.json'
        for result in results
    )


def test_commercial_tools_return_standard_approved_evidence_records():
    app=get_app_download_info.invoke({'reason':'course_discovery'})
    subscription=get_subscription_info.invoke({'reason':'purchase_interest'})
    assert (app['id'],app['kind'],app['status'])==(
        'commercial_app_downloads','commercial','approved',
    )
    assert (subscription['id'],subscription['kind'],subscription['status'])==(
        'commercial_subscription','commercial','approved',
    )
    message=ToolMessage(
        content=json.dumps(app),tool_call_id='commercial',name='get_app_download_info',
    )
    assert agent._evidence_from_messages([message])[0]['id']=='commercial_app_downloads'


def test_current_turn_slice_excludes_prior_tool_messages():
    prior=ToolMessage(content='[]',tool_call_id='old',name='get_support_route')
    current=ToolMessage(content='[]',tool_call_id='new',name='search_course_catalog')
    input_content='VISITOR_QUESTION\n"current"'
    messages=[
        HumanMessage(content='VISITOR_QUESTION\n"prior"'),prior,AIMessage(content='old answer'),
        HumanMessage(content=input_content),current,AIMessage(content='new answer'),
    ]
    turn=agent._current_turn_messages(messages,input_content)
    assert agent._used_tool_names(turn)==['search_course_catalog']


def test_multi_turn_followup_uses_relevant_prior_context_not_prior_tool_calls(monkeypatch,caplog):
    prior_question='What IELTS speaking courses does Eduling offer?'
    prior_input=retrieve_evidence(prior_question).generation_input(prior_question)
    prior_tool=ToolMessage(content='[]',tool_call_id='old',name='get_support_route')

    class HistoryAgent:
        def invoke(self,payload,config):
            return {'messages':[
                HumanMessage(content=prior_input),prior_tool,AIMessage(content='Prior answer'),
                *payload['messages'],AIMessage(content='Eduling offers IELTS writing courses.'),
            ]}

    monkeypatch.setattr(agent,'get_agent',lambda:HistoryAgent())
    monkeypatch.setattr(agent,'get_settings',lambda:SimpleNamespace(max_agent_steps=8,diagnostic_logging=True))
    with caplog.at_level(logging.INFO,logger='backend.agent'):
        result=agent.chat('What about writing?','visitor_followup_context')

    diagnostic=next(record.message for record in caplog.records if record.message.startswith('chat_diagnostic'))
    assert result['status']=='answered'
    assert '"tool_selection":"not_called"' in diagnostic
    assert '"prior_context_records":["tests_ielts_toefl"]' in diagnostic


def test_pronoun_followup_uses_latest_prior_context(monkeypatch,caplog):
    prior_question='Do you have IELTS courses?'
    prior_input=retrieve_evidence(prior_question).generation_input(prior_question)

    class HistoryAgent:
        def invoke(self,payload,config):
            return {'messages':[
                HumanMessage(content=prior_input),AIMessage(content='Prior answer'),
                *payload['messages'],AIMessage(content='They cover IELTS speaking and writing.'),
            ]}

    monkeypatch.setattr(agent,'get_agent',lambda:HistoryAgent())
    monkeypatch.setattr(agent,'get_settings',lambda:SimpleNamespace(max_agent_steps=8,diagnostic_logging=True))
    with caplog.at_level(logging.INFO,logger='backend.agent'):
        result=agent.chat('What skills do they cover?','visitor_pronoun_followup')

    diagnostic=next(record.message for record in caplog.records if record.message.startswith('chat_diagnostic'))
    assert result['status']=='answered'
    assert '"prior_context_records":["tests_ielts_toefl"]' in diagnostic


def test_grounded_ielts_answer_succeeds_with_mocked_agent(monkeypatch):
    evidence=search_course_catalog.invoke({'query':'What IELTS speaking courses does Eduling offer?'})
    fake=FakeAgent([_tool_message(evidence), AIMessage(content='Eduling offers IELTS speaking and writing courses and a TOEFL Speaking course.')])
    monkeypatch.setattr(agent,'get_agent',lambda:fake)

    result=agent.chat('What IELTS speaking courses does Eduling offer?','visitor_test_123')

    assert result['status']=='answered'
    assert {action['type'] for action in result['actions']}=={'download_ios','download_android'}


def test_pre_retrieval_recovers_ielts_when_agent_calls_no_tool(monkeypatch):
    fake=CapturingAgent([AIMessage(content='Eduling offers IELTS speaking and writing courses and a TOEFL Speaking course.')])
    monkeypatch.setattr(agent,'get_agent',lambda:fake)

    result=agent.chat('What IELTS speaking courses does Eduling offer?','visitor_pre_retrieval')

    assert result['status']=='answered'
    assert 'BACKEND_APPROVED_EVIDENCE' in fake.payload['messages'][0].content
    assert 'tests_ielts_toefl' in fake.payload['messages'][0].content


def test_premium_purchase_uses_pre_retrieved_commercial_evidence(monkeypatch):
    fake=FakeAgent([AIMessage(content='Website subscriptions are available through the verified subscription action.')])
    monkeypatch.setattr(agent,'get_agent',lambda:fake)

    result=agent.chat('How do I buy premium?','visitor_premium_purchase')

    assert result['status']=='answered'
    assert {action['type'] for action in result['actions']}=={'subscribe_website'}


def test_partial_website_pricing_answer_is_allowed_but_advantage_claim_is_blocked(monkeypatch,caplog):
    monkeypatch.setattr(agent,'get_settings',lambda:SimpleNamespace(max_agent_steps=8,diagnostic_logging=True))
    safe=FakeAgent([AIMessage(content='Website subscriptions are available, but the website-versus-app price advantage is not verified.')])
    monkeypatch.setattr(agent,'get_agent',lambda:safe)
    with caplog.at_level(logging.INFO,logger='backend.agent'):
        result=agent.chat('Is website pricing cheaper than the app?','visitor_price_partial')
    assert result['status']=='answered'
    assert {action['type'] for action in result['actions']}=={
        'download_ios','download_android','subscribe_website',
    }

    with caplog.at_level(logging.INFO,logger='backend.agent'):
        unsafe=FakeAgent([AIMessage(content='Website pricing is cheaper than in-app pricing.')])
        monkeypatch.setattr(agent,'get_agent',lambda:unsafe)
        result=agent.chat('Is website pricing cheaper than the app?','visitor_price_unsafe')
    assert result['status']=='fallback'
    assert 'cheaper' not in result['answer'].lower()
    diagnostics=[record.message for record in caplog.records if record.message.startswith('chat_diagnostic')]
    assert any('"reason":"partial_evidence"' in message for message in diagnostics)
    assert any('"reason":"validation_failure"' in message for message in diagnostics)


def test_missing_blog_results_use_no_evidence_fallback_reason(monkeypatch,caplog):
    fake=FakeAgent([AIMessage(content='Eduling has no vocabulary blog posts.')])
    monkeypatch.setattr(agent,'get_agent',lambda:fake)
    monkeypatch.setattr(agent,'get_settings',lambda:SimpleNamespace(max_agent_steps=8,diagnostic_logging=True))

    with caplog.at_level(logging.INFO,logger='backend.agent'):
        result=agent.chat('Show me blog posts about vocabulary','visitor_missing_blog')

    diagnostic=next(record.message for record in caplog.records if record.message.startswith('chat_diagnostic'))
    assert result['status']=='fallback'
    assert result['related_articles']==[]
    assert '"reason":"no_evidence"' in diagnostic
    assert '"tool_selection":"not_called"' in diagnostic


def test_agent_tool_evidence_recovers_when_pre_retrieval_fails(monkeypatch,caplog):
    evidence=search_course_catalog.invoke({'query':'What IELTS courses are available?'})
    fake=FakeAgent([_tool_message(evidence),AIMessage(content='Eduling offers IELTS speaking and writing courses.')])
    def fail_retrieval(_question):
        raise RuntimeError('failed')
    monkeypatch.setattr(agent,'retrieve_evidence',fail_retrieval)
    monkeypatch.setattr(agent,'get_agent',lambda:fake)
    monkeypatch.setattr(agent,'get_settings',lambda:SimpleNamespace(max_agent_steps=8,diagnostic_logging=True))

    with caplog.at_level(logging.INFO,logger='backend.agent'):
        result=agent.chat('What IELTS courses are available?','visitor_retrieval_failure')

    diagnostic=next(record.message for record in caplog.records if record.message.startswith('chat_diagnostic'))
    assert result['status']=='answered'
    assert '"pre_retrieval_status":"failed"' in diagnostic
    assert '"tool_selection":"called"' in diagnostic


def test_model_failure_has_distinct_internal_reason(monkeypatch,caplog):
    class GeminiModelError(Exception):
        pass

    class FailingAgent:
        def invoke(self,payload,config):
            raise GeminiModelError('service unavailable')

    monkeypatch.setattr(agent,'get_agent',lambda:FailingAgent())
    monkeypatch.setattr(agent,'get_settings',lambda:SimpleNamespace(max_agent_steps=8,diagnostic_logging=True))

    with caplog.at_level(logging.INFO,logger='backend.agent'):
        result=agent.chat('What is Eduling?','visitor_model_failure')

    diagnostic=next(record.message for record in caplog.records if record.message.startswith('chat_diagnostic'))
    assert result['status']=='unavailable'
    assert '"reason":"model_service_failure"' in diagnostic


def test_unsupported_course_claim_is_rejected(monkeypatch):
    approved_ielts=[{
        'id':'tests_ielts_toefl', 'kind':'faq', 'score':0.9,
        'title':'IELTS and TOEFL', 'content':'IELTS speaking and writing courses and a TOEFL Speaking course.',
        'url':'https://www.eduling.ai/post/course-catalog-in-eduling-speak', 'status':'approved',
    }]
    fake=FakeAgent([_tool_message(approved_ielts), AIMessage(content='Eduling offers a GRE preparation course.')])
    monkeypatch.setattr(agent,'get_agent',lambda:fake)

    result=agent.chat('Do you offer GRE preparation?','visitor_test_456')

    assert result['status']=='fallback'
    assert 'could not verify' in result['answer'].lower()


def test_unverified_japanese_business_course_is_rewritten_as_unknown(monkeypatch):
    irrelevant=search_course_catalog.invoke({'query':'What IELTS courses are available?'})
    fake=FakeAgent([
        _tool_message(irrelevant),
        AIMessage(content=(
            'Eduling focuses on English language learning, including IELTS and TOEFL. '
            'We do not offer courses in Japanese or business courses in other languages.'
        )),
    ])
    monkeypatch.setattr(agent,'get_agent',lambda:fake)

    result=agent.chat(
        'Does Eduling offer an advanced Japanese business course?',
        'visitor_test_japanese',
    )

    assert result['status']=='fallback'
    assert result['answer']==agent.UNKNOWN_COURSE_ANSWER
    assert 'do not offer' not in result['answer'].lower()
    assert {action['type'] for action in result['actions']}=={'download_ios','download_android'}


def test_other_unverified_course_requests_are_not_answered_yes_or_no(monkeypatch):
    fake=FakeAgent([
        _tool_message([]),
        AIMessage(content='No, Eduling does not offer an advanced Klingon course.'),
    ])
    monkeypatch.setattr(agent,'get_agent',lambda:fake)

    result=agent.chat('Do you have an advanced Klingon course?','visitor_test_klingon')

    assert result['answer']==agent.UNKNOWN_COURSE_ANSWER
    assert {action['type'] for action in result['actions']}=={'download_ios','download_android'}


def test_invented_product_feature_recovers_to_curated_answer(monkeypatch):
    evidence=search_course_catalog.invoke({'query':'What IELTS courses are available?'})
    fake=FakeAgent([
        _tool_message(evidence),
        AIMessage(content='Eduling includes virtual reality tutoring and headsets with its IELTS courses.'),
    ])
    monkeypatch.setattr(agent,'get_agent',lambda:fake)

    result=agent.chat('What IELTS courses are available?','visitor_test_product_claim')

    assert result['status']=='answered'
    assert 'virtual reality' not in result['answer'].lower()
    assert 'IELTS speaking and writing' in result['answer']


def test_no_evidence_cannot_ground_fabricated_answer(monkeypatch):
    fake=FakeAgent([_tool_message([]), AIMessage(content='Eduling offers advanced football coaching.')])
    monkeypatch.setattr(agent,'get_agent',lambda:fake)

    result=agent.chat('Who won the football world cup?','visitor_test_789')

    assert result['status']=='fallback'


def test_diagnostics_log_tools_evidence_and_latency_without_visitor_data(monkeypatch,caplog):
    evidence=search_course_catalog.invoke({'query':'What IELTS courses are available?'})
    fake=FakeAgent([_tool_message(evidence), AIMessage(content='Eduling offers IELTS speaking and writing courses.')])
    monkeypatch.setattr(agent,'get_agent',lambda:fake)
    monkeypatch.setattr(agent,'get_settings',lambda:SimpleNamespace(max_agent_steps=8,diagnostic_logging=True))

    with caplog.at_level(logging.INFO,logger='backend.agent'):
        result=agent.chat('What IELTS courses are available?','visitor_private_123')

    diagnostic=next(record.message for record in caplog.records if record.message.startswith('chat_diagnostic'))
    assert result['status']=='answered'
    assert 'search_course_catalog' in diagnostic
    assert 'tests_ielts_toefl' in diagnostic
    assert 'latency_ms' in diagnostic
    assert 'visitor_private_123' not in diagnostic
    assert 'What IELTS courses are available?' not in diagnostic


def test_text_extraction_ignores_non_text_raw_content_blocks():
    content=[
        {'type':'text','text':'A clean answer.'},
        {'type':'tool_use','id':'internal','args':{'secret':'raw output'}},
        {'type':'image','url':'https://example.invalid/internal'},
    ]
    assert agent._text(content)=='A clean answer.'
