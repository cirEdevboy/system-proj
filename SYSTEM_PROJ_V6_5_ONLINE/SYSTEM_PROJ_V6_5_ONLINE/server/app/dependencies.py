from __future__ import annotations
from datetime import datetime, timezone
from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session
from .database import get_db
from .models import User, UserSession, Project
from .security import decode_token
from .master_admin import is_admin_role

def _extract_token(request: Request, authorization: str | None):
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return request.cookies.get("access_token")

def get_current_user(
    request: Request,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    token = _extract_token(request, authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Não autenticado")
    try:
        payload = decode_token(token, "access")
        user_id = int(payload["sub"])
        session_id = payload.get("sid")
    except Exception:
        raise HTTPException(status_code=401, detail="Sessão inválida")
    session = db.get(UserSession, session_id) if session_id else None
    if not session or session.revoked_at:
        raise HTTPException(status_code=401, detail="Sessão encerrada")
    user = db.get(User, user_id)
    if not user or user.deleted_at or user.status != "ACTIVE":
        raise HTTPException(status_code=403, detail="Usuário não está ativo")
    session.last_seen_at = datetime.now(timezone.utc)
    db.commit()
    return user

def require_admin(user: User = Depends(get_current_user)):
    if not is_admin_role(user.role):
        raise HTTPException(
            status_code=403,
            detail="Acesso exclusivo para ADMIN"
        )
    return user

def can_edit_project(project: Project, user: User):
    return (
        is_admin_role(user.role)
        or project.current_responsible_user_id == user.id
    )

def require_project_editor(project: Project, user: User):
    if not can_edit_project(project, user):
        raise HTTPException(status_code=403, detail="Projeto público em modo somente leitura para este usuário")
