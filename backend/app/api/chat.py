"""Chat API: accepts a question (+ optional history) and returns the answer."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agent.graph import ask

router = APIRouter(prefix="/api", tags=["chat"])


class Turn(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="The user's question")
    history: list[Turn] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    try:
        answer = ask(req.message, [t.model_dump() for t in req.history])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent error: {exc}") from exc
    return ChatResponse(answer=answer)
