from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text,
    UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from .database import Base

def utcnow():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    full_name = Column(String(180), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    badge = Column(String(80), unique=True, nullable=False, index=True)
    password_hash = Column(String(500), nullable=False)
    role = Column(String(30), nullable=False, default="OPERATOR")
    status = Column(String(30), nullable=False, default="PENDING")
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    approved_at = Column(DateTime(timezone=True))
    approved_by_id = Column(Integer, ForeignKey("users.id"))
    last_login_at = Column(DateTime(timezone=True))
    deleted_at = Column(DateTime(timezone=True))

class MigrationClaim(Base):
    """
    Código de ativação de uso único para identidades migradas da V5.

    A V5 não possuía e-mail, crachá e senha compatíveis com a V6.
    Por isso a identidade é preservada para manter autoria/responsabilidade,
    mas o próprio colaborador completa seu cadastro na V6 usando um código
    de ativação gerado durante a migração.
    """
    __tablename__ = "migration_claims"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
        index=True,
    )
    token_hash = Column(String(64), unique=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )
    used_at = Column(DateTime(timezone=True))


class UserSession(Base):
    __tablename__ = "user_sessions"
    id = Column(String(64), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    refresh_token_hash = Column(String(64), nullable=False)
    device_name = Column(String(180))
    ip_address = Column(String(80))
    user_agent = Column(String(500))
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    last_seen_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    revoked_at = Column(DateTime(timezone=True))

class PasswordReset(Base):
    __tablename__ = "password_resets"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    os = Column(String(80), unique=True, nullable=False, index=True)
    client = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    initiated_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    current_responsible_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(120), default="NOVO", nullable=False, index=True)
    container_status = Column(String(120), default="AGUARDANDO DEFINIÇÃO DO CONTAINER", nullable=False)
    transport_stage = Column(String(120), default="AGUARDANDO PROGRAMAÇÃO DE TRANSPORTE", nullable=False)
    transfer_requested = Column(Boolean, default=False, nullable=False)
    collection_forecast = Column(String(30))
    consumables_collected = Column(Boolean, default=False, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    deleted_at = Column(DateTime(timezone=True))
    initiator = relationship("User", foreign_keys=[initiated_by_user_id])
    responsible = relationship("User", foreign_keys=[current_responsible_user_id])

class ResponsibilityTransfer(Base):
    __tablename__ = "responsibility_transfers"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    from_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    to_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    requested_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(30), default="PENDING", nullable=False, index=True)
    admin_override = Column(Boolean, default=False, nullable=False)
    requested_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    responded_at = Column(DateTime(timezone=True))

class ResponsibilityHistory(Base):
    __tablename__ = "responsibility_history"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    ended_at = Column(DateTime(timezone=True))
    reason = Column(Text)
    transfer_id = Column(Integer, ForeignKey("responsibility_transfers.id"))

class StageEvent(Base):
    __tablename__ = "stage_events"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    area = Column(String(50), nullable=False, index=True)
    stage = Column(String(160), nullable=False)
    occurred_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    metadata_json = Column(JSON, default=dict)

class Material(Base):
    __tablename__ = "materials"
    __table_args__ = (UniqueConstraint("code", "center", "deposit", name="uq_material_location"),)
    id = Column(Integer, primary_key=True)
    code = Column(String(80), nullable=False, index=True)
    description = Column(String(600), nullable=False, index=True)
    center = Column(String(80), nullable=False, default="")
    deposit = Column(String(80), nullable=False, default="")
    unit = Column(String(30), nullable=False, default="UN")
    active = Column(Boolean, default=True, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

class ProjectItem(Base):
    __tablename__ = "project_items"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    original_description = Column(String(1000), nullable=False)
    quantity = Column(Float, default=1, nullable=False)
    unit = Column(String(30), default="UN", nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"))
    material_code = Column(String(80))
    matched_description = Column(String(1000))
    match_score = Column(Float)
    match_state = Column(String(50), default="NOT_FOUND", nullable=False)
    transfer_eligible = Column(Boolean, default=False, nullable=False)

class RomaneioItem(Base):
    __tablename__ = "romaneio_items"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    category = Column(String(80), nullable=False)
    description = Column(String(1000), nullable=False)
    quantity = Column(Float, default=1, nullable=False)
    unit = Column(String(30), default="UN", nullable=False)
    origin = Column(String(80), default="MANUAL")
    source_document = Column(String(500))
    observation = Column(Text)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    deleted_at = Column(DateTime(timezone=True))

class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (Index("ix_document_project_key", "project_id", "logical_key"),)
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    logical_key = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    filename = Column(String(500), nullable=False)
    storage_key = Column(String(700), nullable=False)
    mime_type = Column(String(200))
    version = Column(Integer, default=1, nullable=False)
    checksum_sha256 = Column(String(64), nullable=False)
    supersedes_id = Column(Integer, ForeignKey("documents.id"))
    uploaded_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    deleted_at = Column(DateTime(timezone=True))

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    kind = Column(String(80), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    payload_json = Column(JSON, default=dict)
    read_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = Column(Integer, primary_key=True)
    actor_user_id = Column(Integer, ForeignKey("users.id"), index=True)
    entity_type = Column(String(80), nullable=False, index=True)
    entity_id = Column(String(100), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)
    old_json = Column(JSON)
    new_json = Column(JSON)
    ip_address = Column(String(80))
    user_agent = Column(String(500))
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
