"""
SYSTEM PROJ V6.1
Migração assistida V5 SQLite -> V6.

Preserva:
- usuários/identidades;
- projetos ativos e excluídos;
- autoria/responsável atual;
- catálogo de materiais;
- itens de projeto;
- romaneio;
- histórico V5 como auditoria;
- datas conhecidas das etapas;
- documentos do projeto;
- planilhas de transferência existentes.

A V5 não armazenava e-mail/crachá/senha compatíveis com a V6.
Usuários que ainda não existirem na V6 são criados como MIGRATED e
recebem um código de ativação de uso único.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import mimetypes
import os
from pathlib import Path
import re
import secrets
import sqlite3
import sys

HERE = Path(__file__).resolve()
SERVER_ROOT = HERE.parent.parent / "server"
if SERVER_ROOT.exists():
    sys.path.insert(0, str(SERVER_ROOT))
else:
    sys.path.insert(0, "/app")

from app.database import Base, engine, SessionLocal
from app.models import (
    AuditEvent,
    Document,
    Material,
    MigrationClaim,
    Project,
    ProjectItem,
    ResponsibilityHistory,
    RomaneioItem,
    StageEvent,
    User,
)
from app.security import hash_password, sha256
from app.services import save_versioned_document, utcnow


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("sqlite_db")
    p.add_argument(
        "--documents-root",
        default="/data/migration/DOCUMENTOS_PROJETOS",
    )
    p.add_argument(
        "--transfers-root",
        default="/data/migration/TRANSFERENCIAS_GERADAS",
    )
    p.add_argument(
        "--report",
        default="/data/migration/relatorio_migracao.json",
    )
    p.add_argument(
        "--activation-csv",
        default="/data/migration/codigos_ativacao_usuarios.csv",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
    )
    p.add_argument(
        "--force",
        action="store_true",
    )
    return p.parse_args()


def now():
    return datetime.now(timezone.utc)


def parse_dt(value):
    if not value:
        return None

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    text = str(value).strip()

    formats = (
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    )

    for fmt in formats:
        try:
            return datetime.strptime(
                text,
                fmt
            ).replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            pass

    return None


def sqlite_tables(con):
    return {
        row[0]
        for row in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }


def row_value(row, key, default=None):
    return (
        row[key]
        if key in row.keys()
        else default
    )


def clean(value):
    return str(
        value or ""
    ).strip()


def bool_value(value):
    try:
        return bool(
            int(value or 0)
        )
    except Exception:
        return bool(value)


def source_fingerprint(path: Path):
    h = hashlib.sha256()

    with path.open("rb") as f:
        while True:
            chunk = f.read(
                1024 * 1024
            )
            if not chunk:
                break
            h.update(chunk)

    return h.hexdigest()


def role_map(value):
    role = clean(
        value
    ).upper()

    if role == "ADMIN":
        return "ADMIN"

    if role == "CONSULTA":
        return "CONSULTA"

    return "OPERATOR"


def unique_placeholder_email(username, suffix):
    safe = re.sub(
        r"[^a-z0-9_.-]+",
        "_",
        username.lower()
    )

    return (
        f"legacy+{safe}+{suffix[:10]}@migrado.invalid"
    )


def resolve_file(
    original_path,
    original_name,
    os_value,
    root: Path,
):
    candidates = []

    if original_path:
        p = Path(
            str(original_path)
        )

        if p.exists():
            candidates.append(
                p
            )

        candidates.append(
            root / p.name
        )

        candidates.append(
            root
            / str(os_value)
            / p.name
        )

    if original_name:
        candidates.append(
            root
            / str(os_value)
            / str(original_name)
        )

        candidates.append(
            root
            / str(original_name)
        )

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate

    wanted = (
        str(original_name).lower()
        if original_name
        else Path(
            str(original_path or "")
        ).name.lower()
    )

    if wanted and root.exists():
        for p in root.rglob("*"):
            if (
                p.is_file()
                and p.name.lower()
                == wanted
            ):
                return p

    return None


def audit_migrated(
    db,
    actor_id,
    entity_type,
    entity_id,
    action,
    old=None,
    new=None,
    created_at=None,
):
    ev = AuditEvent(
        actor_user_id=actor_id,
        entity_type=entity_type,
        entity_id=str(entity_id),
        action=action,
        old_json=old,
        new_json=new,
        created_at=created_at or utcnow(),
    )
    db.add(ev)
    return ev


def add_stage_once(
    db,
    project_id,
    area,
    stage,
    occurred_at,
    user_id,
    metadata=None,
):
    if not occurred_at:
        return False

    exists = db.query(StageEvent).filter(
        StageEvent.project_id == project_id,
        StageEvent.area == area,
        StageEvent.stage == stage,
        StageEvent.occurred_at == occurred_at,
    ).first()

    if exists:
        return False

    db.add(
        StageEvent(
            project_id=project_id,
            area=area,
            stage=stage,
            occurred_at=occurred_at,
            user_id=user_id,
            metadata_json=metadata or {"source": "V5"},
        )
    )

    return True


def main():
    args = parse_args()

    src = Path(
        args.sqlite_db
    )

    if not src.exists():
        raise SystemExit(
            f"Banco V5 não encontrado: {src}"
        )

    fingerprint = source_fingerprint(
        src
    )

    con = sqlite3.connect(
        str(src)
    )

    con.row_factory = (
        sqlite3.Row
    )

    tables = sqlite_tables(
        con
    )

    required = {
        "projetos",
        "usuarios",
    }

    missing_required = (
        required - tables
    )

    if missing_required:
        raise SystemExit(
            "O arquivo não parece ser um banco V5 válido. "
            f"Tabelas ausentes: {sorted(missing_required)}"
        )

    report = {
        "source": str(
            src.resolve()
        ),
        "source_sha256": fingerprint,
        "dry_run": bool(
            args.dry_run
        ),
        "tables_found": sorted(
            tables
        ),
        "counts_source": {},
        "migrated": {
            "users_reused": 0,
            "users_created": 0,
            "activation_codes": 0,
            "materials": 0,
            "projects": 0,
            "deleted_projects": 0,
            "project_items": 0,
            "romaneio_items": 0,
            "history_events": 0,
            "stage_events": 0,
            "documents": 0,
            "transfer_files": 0,
        },
        "warnings": [],
        "missing_files": [],
        "ambiguous_material_codes": [],
    }

    for table_name in (
        "usuarios",
        "projetos",
        "materiais",
        "itens_projeto",
        "romaneio_itens",
        "historico",
        "documentos_projeto",
    ):
        if table_name in tables:
            report[
                "counts_source"
            ][
                table_name
            ] = con.execute(
                f"SELECT COUNT(*) FROM {table_name}"
            ).fetchone()[0]

    if args.dry_run:
        Path(
            args.report
        ).parent.mkdir(
            parents=True,
            exist_ok=True
        )

        Path(
            args.report
        ).write_text(
            json.dumps(
                report,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        print(
            json.dumps(
                report,
                ensure_ascii=False,
                indent=2,
            )
        )

        con.close()
        return

    Base.metadata.create_all(
        bind=engine
    )

    db = SessionLocal()

    activation_rows = []

    try:
        migration_marker = db.query(
            AuditEvent
        ).filter(
            AuditEvent.entity_type == "migration",
            AuditEvent.entity_id == fingerprint,
            AuditEvent.action == "V5_MIGRATION_COMPLETE",
        ).first()

        if (
            migration_marker
            and not args.force
        ):
            raise SystemExit(
                "Este mesmo banco V5 já foi migrado. "
                "Use --force somente se souber exatamente o que está fazendo."
            )

        # ----------------------------------------------------
        # USUÁRIOS / IDENTIDADES
        # ----------------------------------------------------

        user_map = {}

        def get_or_create_user(
            username,
            full_name=None,
            role="OPERATOR",
        ):
            username = clean(
                username
            ).lower()

            if not username:
                username = "migracao"

            if username in user_map:
                return user_map[
                    username
                ]

            existing = db.query(
                User
            ).filter(
                User.username == username
            ).first()

            if existing:
                user_map[
                    username
                ] = existing
                report[
                    "migrated"
                ][
                    "users_reused"
                ] += 1
                return existing

            suffix = secrets.token_hex(
                6
            )

            user = User(
                full_name=(
                    clean(
                        full_name
                    )
                    or username.upper()
                ),
                email=unique_placeholder_email(
                    username,
                    suffix
                ),
                username=username,
                badge=(
                    f"LEGACY-{suffix.upper()}"
                ),
                password_hash=hash_password(
                    secrets.token_urlsafe(
                        32
                    )
                ),
                role=role_map(
                    role
                ),
                status="MIGRATED",
            )

            db.add(
                user
            )

            db.flush()

            activation_code = (
                secrets.token_urlsafe(
                    18
                )
            )

            db.add(
                MigrationClaim(
                    user_id=user.id,
                    token_hash=sha256(
                        activation_code
                    ),
                )
            )

            activation_rows.append({
                "username": username,
                "nome_v5": user.full_name,
                "codigo_ativacao": activation_code,
            })

            user_map[
                username
            ] = user

            report[
                "migrated"
            ][
                "users_created"
            ] += 1

            report[
                "migrated"
            ][
                "activation_codes"
            ] += 1

            return user

        for r in con.execute(
            "SELECT * FROM usuarios"
        ):
            get_or_create_user(
                row_value(
                    r,
                    "username"
                ),
                row_value(
                    r,
                    "nome"
                ),
                row_value(
                    r,
                    "perfil",
                    "OPERATOR"
                ),
            )

        default_user = (
            next(
                iter(
                    user_map.values()
                )
            )
            if user_map
            else get_or_create_user(
                "migracao",
                "Migração V5",
                "ADMIN",
            )
        )

        # Usuários citados nos projetos/histórico mas ausentes da tabela.
        if "projetos" in tables:
            for r in con.execute(
                "SELECT DISTINCT responsavel FROM projetos"
            ):
                resp = clean(
                    r["responsavel"]
                ).lower()

                if resp:
                    get_or_create_user(
                        resp,
                        resp.upper(),
                        "OPERATOR",
                    )

        if "historico" in tables:
            for r in con.execute(
                "SELECT DISTINCT usuario FROM historico"
            ):
                usr = clean(
                    r["usuario"]
                ).lower()

                if usr and usr != "sistema":
                    get_or_create_user(
                        usr,
                        usr.upper(),
                        "OPERATOR",
                    )

        # ----------------------------------------------------
        # MATERIAIS
        # ----------------------------------------------------

        material_by_location = {}

        if "materiais" in tables:
            for r in con.execute(
                "SELECT * FROM materiais"
            ):
                code = clean(
                    row_value(
                        r,
                        "codigo"
                    )
                )

                desc = clean(
                    row_value(
                        r,
                        "descricao"
                    )
                )

                center = clean(
                    row_value(
                        r,
                        "centro"
                    )
                )

                deposit = clean(
                    row_value(
                        r,
                        "deposito"
                    )
                )

                unit = (
                    clean(
                        row_value(
                            r,
                            "unidade",
                            "UN"
                        )
                    )
                    or "UN"
                )

                active = bool_value(
                    row_value(
                        r,
                        "ativo",
                        1
                    )
                )

                if not code or not desc:
                    continue

                mat = db.query(
                    Material
                ).filter(
                    Material.code == code,
                    Material.center == center,
                    Material.deposit == deposit,
                ).first()

                if not mat:
                    mat = Material(
                        code=code,
                        description=desc,
                        center=center,
                        deposit=deposit,
                        unit=unit,
                        active=active,
                    )

                    db.add(
                        mat
                    )

                    db.flush()

                else:
                    mat.description = desc
                    mat.unit = unit
                    mat.active = active

                material_by_location[
                    (
                        code,
                        center,
                        deposit,
                    )
                ] = mat

                report[
                    "migrated"
                ][
                    "materials"
                ] += 1

        # ----------------------------------------------------
        # HISTÓRICO V5 pré-carregado para inferir iniciador
        # ----------------------------------------------------

        history_by_os = {}

        if "historico" in tables:
            for r in con.execute(
                """
                SELECT *
                FROM historico
                ORDER BY id
                """
            ):
                history_by_os.setdefault(
                    clean(
                        r["os"]
                    ),
                    []
                ).append(
                    r
                )

        # ----------------------------------------------------
        # PROJETOS
        # ----------------------------------------------------

        project_map = {}

        for r in con.execute(
            "SELECT * FROM projetos"
        ):
            os_value = clean(
                row_value(
                    r,
                    "os"
                )
            )

            if not os_value:
                continue

            responsible_name = clean(
                row_value(
                    r,
                    "responsavel"
                )
            ).lower()

            responsible = (
                user_map.get(
                    responsible_name
                )
                or get_or_create_user(
                    responsible_name
                    or "migracao",
                    responsible_name.upper()
                    if responsible_name
                    else "Migração V5",
                )
            )

            initiator = responsible

            # Tenta preservar quem efetivamente criou a OS quando houver
            # um registro explícito no histórico da V5.
            for hist in history_by_os.get(
                os_value,
                []
            ):
                action = clean(
                    row_value(
                        hist,
                        "acao"
                    )
                ).upper()

                hist_user = clean(
                    row_value(
                        hist,
                        "usuario"
                    )
                ).lower()

                if (
                    "PROJETO CRIADO" in action
                    and hist_user
                    and hist_user != "sistema"
                ):
                    initiator = (
                        user_map.get(
                            hist_user
                        )
                        or get_or_create_user(
                            hist_user,
                            hist_user.upper(),
                        )
                    )
                    break

            created_at = (
                parse_dt(
                    row_value(
                        r,
                        "data_criacao"
                    )
                )
                or utcnow()
            )

            excluded = bool_value(
                row_value(
                    r,
                    "excluido",
                    0
                )
            )

            deleted_at = (
                parse_dt(
                    row_value(
                        r,
                        "data_exclusao"
                    )
                )
                if excluded
                else None
            )

            project = db.query(
                Project
            ).filter(
                Project.os == os_value
            ).first()

            if not project:
                project = Project(
                    os=os_value,
                    client=(
                        clean(
                            row_value(
                                r,
                                "cliente"
                            )
                        )
                        or "PROJETO"
                    ),
                    title=(
                        clean(
                            row_value(
                                r,
                                "projeto"
                            )
                        )
                        or "PROJETO"
                    ),
                    initiated_by_user_id=initiator.id,
                    current_responsible_user_id=responsible.id,
                    status=(
                        clean(
                            row_value(
                                r,
                                "status"
                            )
                        )
                        or "MIGRADO"
                    ),
                    container_status=(
                        clean(
                            row_value(
                                r,
                                "situacao_container"
                            )
                        )
                        or "AGUARDANDO DEFINIÇÃO DO CONTAINER"
                    ),
                    transport_stage=(
                        clean(
                            row_value(
                                r,
                                "etapa_transporte"
                            )
                        )
                        or "AGUARDANDO PROGRAMAÇÃO DE TRANSPORTE"
                    ),
                    transfer_requested=bool_value(
                        row_value(
                            r,
                            "transferencia_solicitada",
                            0
                        )
                    ),
                    collection_forecast=(
                        clean(
                            row_value(
                                r,
                                "previsao_coleta"
                            )
                        )
                        or None
                    ),
                    consumables_collected=bool_value(
                        row_value(
                            r,
                            "transferencia_coletada",
                            0
                        )
                    ),
                    created_at=created_at,
                    updated_at=created_at,
                    deleted_at=deleted_at,
                )

                db.add(
                    project
                )

                db.flush()

            project_map[
                os_value
            ] = project

            report[
                "migrated"
            ][
                "projects"
            ] += 1

            if excluded:
                report[
                    "migrated"
                ][
                    "deleted_projects"
                ] += 1

            # Responsabilidade atual migrada.
            if not db.query(
                ResponsibilityHistory
            ).filter(
                ResponsibilityHistory.project_id == project.id,
                ResponsibilityHistory.user_id == responsible.id,
                ResponsibilityHistory.ended_at.is_(None),
            ).first():
                db.add(
                    ResponsibilityHistory(
                        project_id=project.id,
                        user_id=responsible.id,
                        started_at=created_at,
                        reason="Responsabilidade migrada da V5",
                    )
                )

            # Evento inicial.
            if add_stage_once(
                db,
                project.id,
                "PROJECT",
                "PROJETO MIGRADO DA V5",
                created_at,
                initiator.id,
                {"source": "V5"},
            ):
                report[
                    "migrated"
                ][
                    "stage_events"
                ] += 1

            transfer_dt = parse_dt(
                row_value(
                    r,
                    "data_solicitacao_transferencia"
                )
            )

            if (
                bool_value(
                    row_value(
                        r,
                        "transferencia_solicitada",
                        0
                    )
                )
                and transfer_dt
                and add_stage_once(
                    db,
                    project.id,
                    "CONSUMABLES",
                    "TRANSFERÊNCIA SOLICITADA",
                    transfer_dt,
                    responsible.id,
                )
            ):
                report[
                    "migrated"
                ][
                    "stage_events"
                ] += 1

            collected_dt = parse_dt(
                row_value(
                    r,
                    "data_coleta"
                )
            )

            if (
                bool_value(
                    row_value(
                        r,
                        "transferencia_coletada",
                        0
                    )
                )
                and collected_dt
                and add_stage_once(
                    db,
                    project.id,
                    "CONSUMABLES",
                    "CONSUMÍVEIS COLETADOS",
                    collected_dt,
                    responsible.id,
                )
            ):
                report[
                    "migrated"
                ][
                    "stage_events"
                ] += 1

            container_dt = parse_dt(
                row_value(
                    r,
                    "data_locacao_container"
                )
            )

            if (
                bool_value(
                    row_value(
                        r,
                        "container_locado",
                        0
                    )
                )
                and container_dt
                and add_stage_once(
                    db,
                    project.id,
                    "CONTAINER",
                    "CONTAINER LOCADO",
                    container_dt,
                    responsible.id,
                )
            ):
                report[
                    "migrated"
                ][
                    "stage_events"
                ] += 1

        # ----------------------------------------------------
        # ITENS DE PROJETO
        # ----------------------------------------------------

        if "itens_projeto" in tables:
            for r in con.execute(
                "SELECT * FROM itens_projeto"
            ):
                project = project_map.get(
                    clean(
                        r["os"]
                    )
                )

                if not project:
                    continue

                code = clean(
                    row_value(
                        r,
                        "codigo"
                    )
                )

                desc = (
                    clean(
                        row_value(
                            r,
                            "descricao_original"
                        )
                    )
                    or clean(
                        row_value(
                            r,
                            "descricao"
                        )
                    )
                    or "ITEM MIGRADO"
                )

                material = None

                if code:
                    candidates = db.query(
                        Material
                    ).filter(
                        Material.code == code
                    ).all()

                    if len(
                        candidates
                    ) == 1:
                        material = candidates[0]

                    elif len(
                        candidates
                    ) > 1:
                        report[
                            "ambiguous_material_codes"
                        ].append({
                            "os": project.os,
                            "codigo": code,
                            "opcoes": [
                                {
                                    "centro": m.center,
                                    "deposito": m.deposit,
                                    "descricao": m.description,
                                }
                                for m in candidates
                            ],
                        })

                existing = db.query(
                    ProjectItem
                ).filter(
                    ProjectItem.project_id == project.id,
                    ProjectItem.original_description == desc,
                    ProjectItem.material_code == (
                        code or None
                    ),
                ).first()

                if existing:
                    continue

                db.add(
                    ProjectItem(
                        project_id=project.id,
                        original_description=desc,
                        quantity=float(
                            row_value(
                                r,
                                "quantidade",
                                1
                            )
                            or 1
                        ),
                        unit=(
                            clean(
                                row_value(
                                    r,
                                    "unidade",
                                    "UN"
                                )
                            )
                            or "UN"
                        ),
                        material_id=(
                            material.id
                            if material
                            else None
                        ),
                        material_code=(
                            code or None
                        ),
                        matched_description=(
                            material.description
                            if material
                            else clean(
                                row_value(
                                    r,
                                    "descricao"
                                )
                            )
                            or None
                        ),
                        match_score=row_value(
                            r,
                            "score_match"
                        ),
                        match_state=(
                            clean(
                                row_value(
                                    r,
                                    "status_match"
                                )
                            )
                            or "MIGRATED"
                        ),
                        transfer_eligible=bool_value(
                            row_value(
                                r,
                                "encontrado",
                                0
                            )
                        ),
                    )
                )

                report[
                    "migrated"
                ][
                    "project_items"
                ] += 1

        # ----------------------------------------------------
        # ROMANEIO
        # ----------------------------------------------------

        if "romaneio_itens" in tables:
            for r in con.execute(
                "SELECT * FROM romaneio_itens"
            ):
                project = project_map.get(
                    clean(
                        r["os"]
                    )
                )

                if not project:
                    continue

                usr = clean(
                    row_value(
                        r,
                        "usuario"
                    )
                ).lower()

                creator = (
                    user_map.get(
                        usr
                    )
                    or default_user
                )

                desc = clean(
                    row_value(
                        r,
                        "descricao"
                    )
                )

                if not desc:
                    continue

                existing = db.query(
                    RomaneioItem
                ).filter(
                    RomaneioItem.project_id == project.id,
                    RomaneioItem.category == (
                        clean(
                            row_value(
                                r,
                                "categoria"
                            )
                        )
                        or "OUTROS"
                    ),
                    RomaneioItem.description == desc,
                    RomaneioItem.quantity == float(
                        row_value(
                            r,
                            "quantidade",
                            1
                        )
                        or 1
                    ),
                ).first()

                if existing:
                    continue

                db.add(
                    RomaneioItem(
                        project_id=project.id,
                        category=(
                            clean(
                                row_value(
                                    r,
                                    "categoria"
                                )
                            )
                            or "OUTROS"
                        ),
                        description=desc,
                        quantity=float(
                            row_value(
                                r,
                                "quantidade",
                                1
                            )
                            or 1
                        ),
                        unit=(
                            clean(
                                row_value(
                                    r,
                                    "unidade",
                                    "UN"
                                )
                            )
                            or "UN"
                        ),
                        origin=(
                            clean(
                                row_value(
                                    r,
                                    "origem",
                                    "MIGRADO"
                                )
                            )
                            or "MIGRADO"
                        ),
                        source_document=(
                            clean(
                                row_value(
                                    r,
                                    "documento_origem"
                                )
                            )
                            or None
                        ),
                        observation=(
                            clean(
                                row_value(
                                    r,
                                    "observacao"
                                )
                            )
                            or None
                        ),
                        created_by_user_id=creator.id,
                        created_at=(
                            parse_dt(
                                row_value(
                                    r,
                                    "incluido_em"
                                )
                            )
                            or utcnow()
                        ),
                    )
                )

                report[
                    "migrated"
                ][
                    "romaneio_items"
                ] += 1

        # ----------------------------------------------------
        # HISTÓRICO V5 -> AUDITORIA
        # ----------------------------------------------------

        if "historico" in tables:
            for r in con.execute(
                "SELECT * FROM historico ORDER BY id"
            ):
                os_value = clean(
                    row_value(
                        r,
                        "os"
                    )
                )

                action = clean(
                    row_value(
                        r,
                        "acao"
                    )
                )

                usr = clean(
                    row_value(
                        r,
                        "usuario"
                    )
                ).lower()

                actor = user_map.get(
                    usr
                )

                source_id = str(
                    row_value(
                        r,
                        "id"
                    )
                )

                exists = db.query(
                    AuditEvent
                ).filter(
                    AuditEvent.entity_type == "v5_history",
                    AuditEvent.entity_id == source_id,
                    AuditEvent.action == "IMPORT",
                ).first()

                if exists:
                    continue

                audit_migrated(
                    db,
                    actor.id if actor else None,
                    "v5_history",
                    source_id,
                    "IMPORT",
                    new={
                        "os": os_value,
                        "acao_original": action,
                        "usuario_original": usr,
                    },
                    created_at=(
                        parse_dt(
                            row_value(
                                r,
                                "data_hora"
                            )
                        )
                        or utcnow()
                    ),
                )

                report[
                    "migrated"
                ][
                    "history_events"
                ] += 1

        # ----------------------------------------------------
        # DOCUMENTOS
        # ----------------------------------------------------

        documents_root = Path(
            args.documents_root
        )

        if "documentos_projeto" in tables:
            for r in con.execute(
                "SELECT * FROM documentos_projeto ORDER BY id"
            ):
                project = project_map.get(
                    clean(
                        r["os"]
                    )
                )

                if not project:
                    continue

                resolved = resolve_file(
                    row_value(
                        r,
                        "caminho"
                    ),
                    row_value(
                        r,
                        "nome_original"
                    ),
                    project.os,
                    documents_root,
                )

                if not resolved:
                    report[
                        "missing_files"
                    ].append({
                        "tipo": "DOCUMENTO",
                        "os": project.os,
                        "nome": clean(
                            row_value(
                                r,
                                "nome_original"
                            )
                        ),
                        "caminho_v5": clean(
                            row_value(
                                r,
                                "caminho"
                            )
                        ),
                    })
                    continue

                usr = clean(
                    row_value(
                        r,
                        "usuario"
                    )
                ).lower()

                uploader = (
                    user_map.get(
                        usr
                    )
                    or default_user
                )

                logical_key = (
                    f"v5-doc-{row_value(r, 'id')}"
                )

                existing = db.query(
                    Document
                ).filter(
                    Document.project_id == project.id,
                    Document.logical_key == logical_key,
                ).first()

                if existing:
                    continue

                data = resolved.read_bytes()

                mime = (
                    mimetypes.guess_type(
                        resolved.name
                    )[0]
                    or "application/octet-stream"
                )

                doc = save_versioned_document(
                    db,
                    project.id,
                    clean(
                        row_value(
                            r,
                            "tipo",
                            "OUTROS"
                        )
                    )
                    or "OUTROS",
                    clean(
                        row_value(
                            r,
                            "nome_original"
                        )
                    )
                    or resolved.name,
                    data,
                    mime,
                    uploader.id,
                    logical_key=logical_key,
                )

                created = parse_dt(
                    row_value(
                        r,
                        "data_inclusao"
                    )
                )

                if created:
                    doc.created_at = created

                report[
                    "migrated"
                ][
                    "documents"
                ] += 1

        # ----------------------------------------------------
        # PLANILHAS DE TRANSFERÊNCIA EXISTENTES
        # ----------------------------------------------------

        transfers_root = Path(
            args.transfers_root
        )

        for r in con.execute(
            "SELECT * FROM projetos"
        ):
            project = project_map.get(
                clean(
                    r["os"]
                )
            )

            if not project:
                continue

            caminho_excel = clean(
                row_value(
                    r,
                    "caminho_excel"
                )
            )

            if not caminho_excel:
                continue

            resolved = resolve_file(
                caminho_excel,
                Path(
                    caminho_excel
                ).name,
                project.os,
                transfers_root,
            )

            if not resolved:
                report[
                    "missing_files"
                ].append({
                    "tipo": "TRANSFERENCIA_XLSX",
                    "os": project.os,
                    "nome": Path(
                        caminho_excel
                    ).name,
                    "caminho_v5": caminho_excel,
                })
                continue

            logical_key = (
                "transferencia-v5"
            )

            existing = db.query(
                Document
            ).filter(
                Document.project_id == project.id,
                Document.logical_key == logical_key,
            ).first()

            if existing:
                continue

            save_versioned_document(
                db,
                project.id,
                "TRANSFERENCIA_XLSX",
                resolved.name,
                resolved.read_bytes(),
                (
                    mimetypes.guess_type(
                        resolved.name
                    )[0]
                    or "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                ),
                project.current_responsible_user_id,
                logical_key=logical_key,
            )

            report[
                "migrated"
            ][
                "transfer_files"
            ] += 1

        # ----------------------------------------------------
        # MARCADOR FINAL
        # ----------------------------------------------------

        audit_migrated(
            db,
            None,
            "migration",
            fingerprint,
            "V5_MIGRATION_COMPLETE",
            new=report["migrated"],
        )

        db.commit()

        # Códigos de ativação são gravados fora do banco em texto claro
        # somente para o administrador distribuir aos usuários migrados.
        activation_path = Path(
            args.activation_csv
        )

        activation_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with activation_path.open(
            "w",
            newline="",
            encoding="utf-8-sig",
        ) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "username",
                    "nome_v5",
                    "codigo_ativacao",
                ],
                delimiter=";",
            )

            writer.writeheader()
            writer.writerows(
                activation_rows
            )

        report_path = Path(
            args.report
        )

        report_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        report_path.write_text(
            json.dumps(
                report,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        print(
            "MIGRACAO_V5_V6_OK"
        )

        print(
            json.dumps(
                report["migrated"],
                ensure_ascii=False,
                indent=2,
            )
        )

        print(
            f"Relatório: {report_path}"
        )

        print(
            f"Códigos de ativação: {activation_path}"
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
        con.close()


if __name__ == "__main__":
    main()
