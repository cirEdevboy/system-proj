from __future__ import annotations

from sqlalchemy.orm import Session

from .config import settings
from .models import AuditEvent, MigrationClaim, User, utcnow
from .security import hash_password


ADMIN_ROLES = (
    "ADMIN",
    "MASTER_ADMIN",
)


def is_admin_role(role: str | None) -> bool:
    return str(role or "").upper() in ADMIN_ROLES


def is_master_admin(user: User | None) -> bool:
    return bool(
        user
        and user.role == "MASTER_ADMIN"
    )


def _required_master_fields():
    return {
        "MASTER_ADMIN_USERNAME": settings.master_admin_username,
        "MASTER_ADMIN_EMAIL": settings.master_admin_email,
        "MASTER_ADMIN_BADGE": settings.master_admin_badge,
        "MASTER_ADMIN_FULL_NAME": settings.master_admin_full_name,
        "MASTER_ADMIN_PASSWORD": settings.master_admin_password,
    }


def ensure_master_admin(
    db: Session,
) -> User | None:
    """
    Bootstrap seguro do MASTER_ADMIN.

    Em produção, os dados vêm de variáveis secretas do Render.
    A senha NÃO é armazenada no código/repositório.

    Se o usuário já é MASTER_ADMIN, o startup não redefine a senha.
    """
    if not settings.master_admin_enabled:
        return db.query(User).filter(
            User.role == "MASTER_ADMIN",
            User.deleted_at.is_(None),
        ).first()

    values = _required_master_fields()
    missing = [
        key
        for key, value in values.items()
        if not str(value or "").strip()
    ]

    if missing:
        raise RuntimeError(
            "MASTER_ADMIN_ENABLED=true, mas faltam variáveis: "
            + ", ".join(missing)
        )

    username = settings.master_admin_username.strip().lower()
    email = settings.master_admin_email.strip().lower()
    badge = settings.master_admin_badge.strip()
    full_name = settings.master_admin_full_name.strip()

    user = db.query(User).filter(
        User.username == username
    ).first()

    email_owner = db.query(User).filter(
        User.email == email
    ).first()

    badge_owner = db.query(User).filter(
        User.badge == badge
    ).first()

    if user is None:
        candidates = [
            x
            for x in (
                email_owner,
                badge_owner,
            )
            if x is not None
        ]

        unique_ids = {
            x.id
            for x in candidates
        }

        if len(unique_ids) > 1:
            raise RuntimeError(
                "Conflito no bootstrap MASTER_ADMIN: "
                "e-mail e crachá pertencem a contas diferentes."
            )

        if candidates:
            user = candidates[0]

    if user is not None:
        if (
            email_owner is not None
            and email_owner.id != user.id
        ):
            raise RuntimeError(
                "O e-mail do MASTER_ADMIN já pertence a outro usuário."
            )

        if (
            badge_owner is not None
            and badge_owner.id != user.id
        ):
            raise RuntimeError(
                "O crachá do MASTER_ADMIN já pertence a outro usuário."
            )

    created = False
    promoted = False

    if user is None:
        user = User(
            full_name=full_name,
            email=email,
            username=username,
            badge=badge,
            password_hash=hash_password(
                settings.master_admin_password
            ),
            role="MASTER_ADMIN",
            status="ACTIVE",
            approved_at=utcnow(),
        )

        db.add(user)
        db.flush()

        user.approved_by_id = user.id
        created = True

    else:
        was_master = (
            user.role == "MASTER_ADMIN"
        )

        user.full_name = full_name
        user.email = email
        user.username = username
        user.badge = badge
        user.role = "MASTER_ADMIN"
        user.status = "ACTIVE"
        user.deleted_at = None
        user.approved_at = (
            user.approved_at
            or utcnow()
        )
        user.approved_by_id = user.id

        if not was_master:
            user.password_hash = hash_password(
                settings.master_admin_password
            )
            promoted = True

        db.flush()

    db.query(MigrationClaim).filter(
        MigrationClaim.user_id == user.id
    ).delete(
        synchronize_session=False
    )

    if created or promoted:
        db.add(
            AuditEvent(
                actor_user_id=user.id,
                entity_type="user",
                entity_id=str(user.id),
                action=(
                    "MASTER_ADMIN_CREATED"
                    if created
                    else "MASTER_ADMIN_PROMOTED"
                ),
                new_json={
                    "username": user.username,
                    "role": user.role,
                    "status": user.status,
                },
            )
        )

    db.commit()
    db.refresh(user)

    return user
