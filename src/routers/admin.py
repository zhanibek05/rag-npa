import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from src.core.auth import require_admin
    from src.core.database import get_db
    from src.core.models import User, ChatSession, ChatMessage
except ModuleNotFoundError:
    from core.auth import require_admin
    from core.database import get_db
    from core.models import User, ChatSession, ChatMessage

router = APIRouter(prefix="/admin", tags=["admin"])


class UserAdminResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    is_active: bool
    is_verified: bool
    created_at: str


class UpdateUserRequest(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/users", response_model=List[UserAdminResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [
        UserAdminResponse(
            id=str(u.id),
            username=u.username,
            email=u.email,
            role=u.role,
            is_active=u.is_active,
            is_verified=u.is_verified,
            created_at=u.created_at.isoformat(),
        )
        for u in users
    ]


@router.patch("/users/{user_id}", response_model=UserAdminResponse)
async def update_user(
    user_id: str,
    req: UpdateUserRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if req.role is not None:
        if req.role not in ("admin", "user"):
            raise HTTPException(status_code=400, detail="Role must be 'admin' or 'user'")
        user.role = req.role
    if req.is_active is not None:
        user.is_active = req.is_active

    await db.commit()
    await db.refresh(user)
    return UserAdminResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at.isoformat(),
    )


@router.get("/stats")
async def stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    users_count = (await db.execute(select(func.count(User.id)))).scalar()
    sessions_count = (await db.execute(select(func.count(ChatSession.id)))).scalar()
    messages_count = (await db.execute(select(func.count(ChatMessage.id)))).scalar()
    return {
        "users": users_count,
        "sessions": sessions_count,
        "messages": messages_count,
    }


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    _: User = Depends(require_admin),
):
    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in {"pdf", "csv", "txt", "docx"}:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")
    content = await file.read()
    # Parsers will be implemented in core/parsers.py
    return {"message": f"Received {filename} ({len(content)} bytes). Parsing coming soon."}