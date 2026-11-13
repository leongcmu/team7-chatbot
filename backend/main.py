"""HTTP adapter for Jianing's frontend. Business logic stays outside routes."""
from uuid import uuid4
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .schemas import ChatRequest, ChatResponse
from .agent import chat

app=FastAPI(title='Eduling Assistant API',version='0.1.0')
settings=get_settings()
app.add_middleware(CORSMiddleware,allow_origins=list(settings.allowed_origins),
                   allow_credentials=False,allow_methods=['POST','GET'],allow_headers=['Content-Type'])

@app.get('/health')
def health():
    """Liveness check; does not expose configuration or secrets."""
    return {'status':'ok'}

@app.post('/chat',response_model=ChatResponse)
def post_chat(request: ChatRequest):
    """Return a grounded answer plus verified UI actions."""
    result=chat(request.message,request.session_id)
    return ChatResponse(**result,request_id=str(uuid4()))
