from __future__ import annotations

import argparse
import getpass
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser


ROOT = Path(__file__).resolve().parent
SERVER_DIR = ROOT / "server"
SCRIPTS_DIR = ROOT / "scripts"

LOCALAPPDATA = os.environ.get("LOCALAPPDATA")
if LOCALAPPDATA:
    USER_ROOT = Path(LOCALAPPDATA) / "SYSTEM_PROJ_V6_TEST"
else:
    USER_ROOT = Path.home() / "SYSTEM_PROJ_V6_TEST"

DATA_DIR = USER_ROOT / "data"
FILES_DIR = USER_ROOT / "files"
LOGS_DIR = USER_ROOT / "logs"
DB_PATH = DATA_DIR / "system_proj_v6_corporativo.db"
SECRET_PATH = DATA_DIR / ".jwt_secret"


def ensure_dirs():
    for pasta in (USER_ROOT, DATA_DIR, FILES_DIR, LOGS_DIR):
        pasta.mkdir(parents=True, exist_ok=True)


def ensure_secret() -> str:
    ensure_dirs()

    if SECRET_PATH.exists():
        secret = SECRET_PATH.read_text(
            encoding="utf-8"
        ).strip()

        if len(secret) >= 32:
            return secret

    secret = secrets.token_urlsafe(48)
    SECRET_PATH.write_text(
        secret,
        encoding="utf-8"
    )
    return secret


def configure_environment():
    ensure_dirs()

    # Caminho absoluto em formato compatível com SQLAlchemy/Windows.
    db_url = "sqlite:///" + DB_PATH.resolve().as_posix()

    os.environ["APP_NAME"] = "SYSTEM PROJ"
    os.environ["ENV"] = "corporate-local-test"
    os.environ["DOMAIN"] = "127.0.0.1"
    os.environ["DATABASE_URL"] = db_url
    os.environ["JWT_SECRET"] = ensure_secret()
    os.environ["ACCESS_TOKEN_MINUTES"] = "60"
    os.environ["REFRESH_TOKEN_DAYS"] = "30"
    os.environ["CORS_ORIGINS"] = (
        "http://127.0.0.1:8000,"
        "http://localhost:8000"
    )
    os.environ["STORAGE_MODE"] = "local"
    os.environ["LOCAL_STORAGE_PATH"] = str(
        FILES_DIR.resolve()
    )
    os.environ["WEB_BASE_URL"] = "http://127.0.0.1:8000"

    # Não usa SMTP no teste corporativo.
    os.environ["SMTP_HOST"] = ""


def add_server_path():
    server = str(SERVER_DIR.resolve())

    if server not in sys.path:
        sys.path.insert(0, server)


def doctor():
    print("=" * 62)
    print("SYSTEM PROJ V6.2 - DIAGNÓSTICO DO PC CORPORATIVO")
    print("=" * 62)
    print()
    print("Python:", sys.version.replace("\n", " "))
    print("Executável:", sys.executable)
    print("Usuário Windows:", getpass.getuser())
    print("Pasta de dados:", USER_ROOT)
    print()

    if sys.version_info < (3, 11):
        print("[ERRO] É necessário Python 3.11 ou superior.")
        return 2

    ensure_dirs()

    teste = DATA_DIR / "_teste_escrita.txt"

    try:
        teste.write_text("OK", encoding="utf-8")
        teste.unlink(missing_ok=True)
        print("[OK] Escrita na pasta do usuário.")
    except Exception as exc:
        print("[ERRO] Sem permissão para gravar dados:", exc)
        return 3

    modulos = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "pydantic_settings",
        "jwt",
        "argon2",
        "multipart",
        "openpyxl",
        "docx",
        "reportlab",
        "jinja2",
        "email_validator",
    ]

    faltando = []

    for modulo in modulos:
        try:
            __import__(modulo)
            print(f"[OK] {modulo}")
        except Exception:
            faltando.append(modulo)
            print(f"[FALTA] {modulo}")

    print()

    if faltando:
        print(
            "Dependências ainda não instaladas. "
            "Execute PREPARAR_PC_CORPORATIVO.bat."
        )
        return 4

    configure_environment()
    add_server_path()

    try:
        from app.database import Base, engine, SessionLocal
        from app.master_admin import ensure_master_admin

        Base.metadata.create_all(bind=engine)

        with SessionLocal() as db:
            master = ensure_master_admin(db)
            print(
                f"[OK] MASTER_ADMIN ativo: {master.username} "
                f"({master.full_name})."
            )

        print("[OK] Banco SQLite V6 inicializado.")
    except Exception as exc:
        print("[ERRO] Banco/API:", exc)
        return 5

    print()
    print("DIAGNÓSTICO CONCLUÍDO COM SUCESSO.")
    print("Nenhum serviço do Windows ou permissão de administrador é usado.")
    return 0


def open_browser_when_ready():
    url = "http://127.0.0.1:8000"

    for _ in range(40):
        try:
            with urllib.request.urlopen(
                url + "/api/v1/health",
                timeout=1
            ) as response:
                if response.status == 200:
                    webbrowser.open(url)
                    return
        except Exception:
            time.sleep(0.5)

    print(
        "Servidor iniciou, mas o navegador não abriu automaticamente."
    )
    print("Abra manualmente:", url)


def server():
    configure_environment()
    add_server_path()

    try:
        import uvicorn
    except Exception:
        print(
            "Uvicorn não instalado. "
            "Execute PREPARAR_PC_CORPORATIVO.bat primeiro."
        )
        return 4

    print("=" * 62)
    print("SYSTEM PROJ V6.2 - TESTE CORPORATIVO")
    print("=" * 62)
    print()
    print("Servidor: http://127.0.0.1:8000")
    print("Banco:", DB_PATH)
    print("Arquivos:", FILES_DIR)
    print()
    print(
        "IMPORTANTE: este modo usa somente este computador. "
        "Não é o servidor online definitivo."
    )
    print()
    print("Para encerrar, feche esta janela ou pressione CTRL+C.")
    print()

    threading.Thread(
        target=open_browser_when_ready,
        daemon=True
    ).start()

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        app_dir=str(SERVER_DIR),
        reload=False,
        access_log=False,
    )

    return 0


def admin():
    configure_environment()
    add_server_path()

    from app.database import Base, engine, SessionLocal
    from app.models import User
    from app.security import hash_password

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        print("=" * 62)
        print("CRIAR ADMIN LOCAL - SYSTEM PROJ V6.2")
        print("=" * 62)
        print()
        print(
            "Se você já usava a V5, prefira o MESMO username "
            "para manter o vínculo na migração."
        )
        print()

        full_name = input("Nome completo: ").strip()
        email = input("E-mail: ").strip().lower()
        username = input("Usuário: ").strip().lower()
        badge = input("Crachá: ").strip()
        password = getpass.getpass(
            "Senha (mínimo 8 caracteres): "
        )

        if len(password) < 8:
            raise SystemExit(
                "A senha precisa ter no mínimo 8 caracteres."
            )

        existing = db.query(User).filter(
            User.username == username
        ).first()

        if existing:
            if existing.role == "ADMIN":
                print(
                    "Este usuário já existe como ADMIN."
                )
                return 0

            raise SystemExit(
                "Este username já existe no banco."
            )

        user = User(
            full_name=full_name,
            email=email,
            username=username,
            badge=badge,
            password_hash=hash_password(password),
            role="ADMIN",
            status="ACTIVE",
        )

        db.add(user)
        db.commit()

        print()
        print("ADMIN criado com sucesso.")
        return 0

    finally:
        db.close()


def backup():
    configure_environment()
    ensure_dirs()

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    destino = USER_ROOT / "backups" / timestamp
    destino.mkdir(parents=True, exist_ok=True)

    if DB_PATH.exists():
        shutil.copy2(
            DB_PATH,
            destino / DB_PATH.name
        )

    if FILES_DIR.exists():
        files_backup = destino / "files"
        shutil.copytree(
            FILES_DIR,
            files_backup,
            dirs_exist_ok=True
        )

    print("Backup criado em:")
    print(destino)
    return 0


def migrate():
    configure_environment()

    migration_dir = ROOT / "migration_data"
    sqlite_db = migration_dir / "gestao_projetos.db"

    if not sqlite_db.exists():
        print(
            "Banco V5 não encontrado em:"
        )
        print(sqlite_db)
        print()
        print(
            "Copie uma CÓPIA do gestao_projetos.db da V5 "
            "para migration_data."
        )
        return 2

    script = SCRIPTS_DIR / "migrate_v5_sqlite.py"

    docs = migration_dir / "DOCUMENTOS_PROJETOS"
    transfers = migration_dir / "TRANSFERENCIAS_GERADAS"
    report_pre = migration_dir / "relatorio_pre_migracao.json"
    report = migration_dir / "relatorio_migracao.json"
    activation = migration_dir / "codigos_ativacao_usuarios.csv"

    print("=" * 62)
    print("ANÁLISE DA MIGRAÇÃO V5 -> V6 LOCAL")
    print("=" * 62)

    cmd_pre = [
        sys.executable,
        str(script),
        str(sqlite_db),
        "--documents-root",
        str(docs),
        "--transfers-root",
        str(transfers),
        "--report",
        str(report_pre),
        "--dry-run",
    ]

    result = subprocess.run(
        cmd_pre,
        cwd=str(ROOT),
    )

    if result.returncode != 0:
        print()
        print("A análise falhou. Nenhum dado foi migrado.")
        return result.returncode

    print()
    print("Relatório prévio:")
    print(report_pre)
    print()

    confirm = input(
        "Executar a migração REAL agora? [S/N]: "
    ).strip().upper()

    if confirm not in ("S", "SIM", "Y", "YES"):
        print("Migração cancelada.")
        return 0

    # Backup automático antes de migrar.
    backup()

    cmd = [
        sys.executable,
        str(script),
        str(sqlite_db),
        "--documents-root",
        str(docs),
        "--transfers-root",
        str(transfers),
        "--report",
        str(report),
        "--activation-csv",
        str(activation),
    ]

    result = subprocess.run(
        cmd,
        cwd=str(ROOT),
    )

    if result.returncode == 0:
        print()
        print("MIGRAÇÃO CONCLUÍDA.")
        print("Relatório:", report)
        print("Códigos de ativação:", activation)

    return result.returncode


def locations():
    ensure_dirs()
    print("Pasta de dados:")
    print(USER_ROOT)
    print()
    print("Banco:")
    print(DB_PATH)
    print()
    print("Documentos/arquivos:")
    print(FILES_DIR)
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=[
            "doctor",
            "server",
            "admin",
            "backup",
            "migrate",
            "locations",
        ],
    )

    args = parser.parse_args()

    commands = {
        "doctor": doctor,
        "server": server,
        "admin": admin,
        "backup": backup,
        "migrate": migrate,
        "locations": locations,
    }

    raise SystemExit(
        commands[args.command]()
    )


if __name__ == "__main__":
    main()
