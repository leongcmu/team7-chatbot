"""Public API contract. Keep stable so frontend and backend evolve independently."""
from typing import Literal
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(min_length=1,max_length=1500)
    session_id: str = Field(min_length=12,max_length=128,pattern=r'^[A-Za-z0-9_-]+$')

class Action(BaseModel):
    type: Literal['download_ios','download_android','subscribe_website']
    label: str
    url: str

class Article(BaseModel):
    title: str
    url: str
    summary: str = ''

class ChatResponse(BaseModel):
    answer: str
    status: Literal['answered','fallback','blocked','unavailable']
    actions: list[Action] = Field(default_factory=list)
    related_articles: list[Article] = Field(default_factory=list)
    request_id: str
