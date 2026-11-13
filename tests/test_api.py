"""API contract tests with the agent mocked to avoid paid model calls."""
from fastapi.testclient import TestClient
from backend.main import app

def test_health():
    assert TestClient(app).get('/health').json()=={'status':'ok'}

def test_chat_contract(monkeypatch):
    from backend import main
    monkeypatch.setattr(main,'chat',lambda m,s:{'answer':'Example','status':'answered','actions':[],'related_articles':[]})
    response=TestClient(app).post('/chat',json={'message':'Hello','session_id':'visitor_test_123'})
    assert response.status_code==200
    assert response.json()['answer']=='Example'
    assert response.json()['request_id']

def test_invalid_session():
    response=TestClient(app).post('/chat',json={'message':'Hello','session_id':'a'})
    assert response.status_code==422
