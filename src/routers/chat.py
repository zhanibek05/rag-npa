import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

try:
    from src.core.auth import get_current_user
    from src.core.database import get_db
    from src.core.models import ChatMessage, ChatSession, User
except ModuleNotFoundError:
    from core.auth import get_current_user
    from core.database import get_db
    from core.models import ChatMessage, ChatSession, User

router = APIRouter(prefix="/chat", tags=["chat"])


class SessionCreate(BaseModel):
    title: Optional[str] = None


class SessionResponse(BaseModel):
    id: str
    title: Optional[str]
    created_at: str
    updated_at: str


class MessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    text: str
    sources: Optional[list] = None
    created_at: str


class SessionWithMessages(BaseModel):
    id: str
    title: Optional[str]
    messages: List[MessageResponse]


class SaveMessageRequest(BaseModel):
    session_id: str
    role: str
    text: str
    sources: Optional[list] = None


# ── helpers ────────────────────────────────────────────────────────────────

def _session_resp(s: ChatSession) -> SessionResponse:
    return SessionResponse(
        id=str(s.id),
        title=s.title,
        created_at=s.created_at.isoformat(),
        updated_at=s.updated_at.isoformat(),
    )


def _msg_resp(m: ChatMessage) -> MessageResponse:
    return MessageResponse(
        id=str(m.id),
        session_id=str(m.session_id),
        role=m.role,
        text=m.text,
        sources=m.sources,
        created_at=m.created_at.isoformat(),
    )


def _parse_uuid(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")


# ── routes ─────────────────────────────────────────────────────────────────

@router.post("/sessions", response_model=SessionResponse, status_code=201)
async def create_session(
    req: SessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = ChatSession(id=uuid.uuid4(), user_id=current_user.id, title=req.title)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return _session_resp(session)


@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
    )
    return [_session_resp(s) for s in result.scalars().all()]


@router.get("/sessions/{session_id}", response_model=SessionWithMessages)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sid = _parse_uuid(session_id)
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.id == sid, ChatSession.user_id == current_user.id)
        .options(selectinload(ChatSession.messages))
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = sorted(session.messages, key=lambda m: m.created_at)
    return SessionWithMessages(
        id=str(session.id),
        title=session.title,
        messages=[_msg_resp(m) for m in messages],
    )


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sid = _parse_uuid(session_id)
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == sid, ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.delete(session)
    await db.commit()


@router.post("/messages", response_model=MessageResponse, status_code=201)
async def save_message(
    req: SaveMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sid = _parse_uuid(req.session_id)
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == sid, ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    message = ChatMessage(
        id=uuid.uuid4(),
        session_id=sid,
        role=req.role,
        text=req.text,
        sources=req.sources,
    )
    db.add(message)
    session.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(message)
    return _msg_resp(message)
