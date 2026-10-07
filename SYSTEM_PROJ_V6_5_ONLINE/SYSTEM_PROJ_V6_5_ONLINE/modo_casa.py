from __future__ import annotations

import argparse
import getpass
import os
from pathlib import Path
import re
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
TOOLS_DIR = ROOT / "tools"

LOCALAPPDATA = os.environ.get("LOCALAPPDATA")
if LOCALAPPDATA:
    USER_ROOT = Path(LOCALAPPDATA) / "SYSTEM_PROJ_V6_HOME_SERVER"
else:
    USER_ROOT = Path.home() / "SYSTEM_PROJ_V6_HOME_SERVER"

DATA_DIR = USER_ROOT / "data"
FILES_DIR = USER_ROOT / "files"
BACKUPS_DIR = USER_ROOT / "backups"
DB_PATH = DATA_DIR / "system_proj_v6_home.db"
SECRET_PATH = DATA_DIR / ".jwt_secret"
URL_FILE = ROOT / "URL_ACESSO_EMPRESA.txt"
CLOUDFLARED = TOOLS_DIR / "cloudflared.exe"


def ensure_dirs():
    for path in (
        USER_ROOT,
        DATA_DIR,
        FILES_DIR,
        BACKUPS_DIR,
        TOOLS_DIR,
    ):
        path.mkdir(
            parents=True,
            exist_ok=True,
        )


def ensure_secret():
    ensure_dirs()

    if SECRET_PATH.exists():
        secret = SECRET_PATH.read_text(
            encoding="utf-8"
        ).strip()

        if len(secret) >= 32:
            return secret

    secret = secrets.token_urlsafe(
        48
    )

    SECRET_PATH.write_text(
        secret,
        encoding="utf-8"
    )

    return secret


def configure_environment():
    ensure_dirs()

    os.environ["APP_NAME"] = "SYSTEM PROJ"
    os.environ["ENV"] = "home-remote-test"
    os.environ["DOMAIN"] = "127.0.0.1"
    os.environ["DATABASE_URL"] = (
        "sqlite:///"
        + DB_PATH.resolve().as_posix()
    )
    os.environ["JWT_SECRET"] = ensure_secret()
    os.environ["ACCESS_TOKEN_MINUTES"] = "60"
    os.environ["REFRESH_TOKEN_DAYS"] = "30"
    os.environ["CORS_ORIGINS"] = "*"
    os.environ["STORAGE_MODE"] = "local"
    os.environ["LOCAL_STORAGE_PATH"] = str(
        FILES_DIR.resolve()
    )
    os.environ["WEB_BASE_URL"] = (
        "http://127.0.0.1:8000"
    )
    os.environ["SMTP_HOST"] = ""


def add_server_path():
    path = str(
        SERVER_DIR.resolve()
    )

    if path not in sys.path:
        sys.path.insert(
            0,
            path,
        )


def wait_health(timeout=30):
    url = (
        "http://127.0.0.1:8000"
        "/api/v1/health"
    )

    deadline = (
        time.time()
        + timeout
    )

    while time.time() < deadline:
        try:
            with urllib.request.urlopen(
                url,
                timeout=1,
            ) as response:
                if response.status == 200:
                    return True
        except Exception:
            time.sleep(
                0.5
            )

    return False


def server():
    configure_environment()
    add_server_path()

    import uvicorn

    print("=" * 64)
    print("SYSTEM PROJ V6.3 - SERVIDOR NO PC DE CASA")
    print("=" * 64)
    print()
    print("Acesso local: http://127.0.0.1:8000")
    print("Banco:", DB_PATH)
    print("Arquivos:", FILES_DIR)
    print()
    print(
        "Este processo precisa permanecer aberto para o sistema funcionar."
    )
    print()

    def open_local():
        if wait_health():
            webbrowser.open(
                "http://127.0.0.1:8000"
            )

    threading.Thread(
        target=open_local,
        daemon=True,
    ).start()

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        app_dir=str(SERVER_DIR),
        reload=False,
        access_log=False,
    )


def download_cloudflared():
    ensure_dirs()

    if CLOUDFLARED.exists():
        print(
            "cloudflared já existe:"
        )
        print(
            CLOUDFLARED
        )
        return 0

    url = (
        "https://github.com/cloudflare/cloudflared/"
        "releases/latest/download/"
        "cloudflared-windows-amd64.exe"
    )

    print(
        "Baixando cloudflared oficial..."
    )

    try:
        urllib.request.urlretrieve(
            url,
            CLOUDFLARED,
        )
    except Exception as exc:
        print(
            "Falha ao baixar cloudflared:"
        )
        print(
            exc
        )
        return 2

    print(
        "cloudflared salvo em:"
    )
    print(
        CLOUDFLARED
    )

    return 0


def external():
    configure_environment()
    ensure_dirs()

    if not CLOUDFLARED.exists():
        code = download_cloudflared()

        if code:
            return code

    server_proc = subprocess.Popen(
        [
            sys.executable,
            str(
                Path(__file__).resolve()
            ),
            "server",
        ],
        cwd=str(ROOT),
    )

    try:
        if not wait_health(
            timeout=40
        ):
            print(
                "O servidor local não respondeu."
            )
            return 3

        print()
        print(
            "Criando acesso HTTPS temporário..."
        )
        print()

        tunnel_proc = subprocess.Popen(
            [
                str(CLOUDFLARED),
                "tunnel",
                "--url",
                "http://127.0.0.1:8000",
                "--no-autoupdate",
            ],
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        public_url = None

        for line in tunnel_proc.stdout:
            print(
                line,
                end="",
            )

            match = re.search(
                r"https://[a-zA-Z0-9-]+\.trycloudflare\.com",
                line,
            )

            if (
                match
                and public_url is None
            ):
                public_url = match.group(
                    0
                )

                URL_FILE.write_text(
                    public_url
                    + "\n",
                    encoding="utf-8",
                )

                print()
                print("=" * 64)
                print(
                    "LINK PARA ABRIR NO PC DA EMPRESA:"
                )
                print(
                    public_url
                )
                print("=" * 64)
                print()
                print(
                    "O link também foi salvo em:"
                )
                print(
                    URL_FILE
                )
                print()
                print(
                    "ATENÇÃO: este link muda quando o túnel é reiniciado."
                )
                print(
                    "Mantenha esta janela e o PC de casa ligados."
                )
                print()

        return tunnel_proc.wait()

    except KeyboardInterrupt:
        return 0

    finally:
        try:
            server_proc.terminate()
        except Exception:
            pass


def backup():
    configure_environment()
    ensure_dirs()

    stamp = time.strftime(
        "%Y%m%d_%H%M%S"
    )

    destination = (
        BACKUPS_DIR
        / stamp
    )

    destination.mkdir(
        parents=True,
        exist_ok=True,
    )

    if DB_PATH.exists():
        shutil.copy2(
            DB_PATH,
            destination
            / DB_PATH.name,
        )

    if FILES_DIR.exists():
        shutil.copytree(
            FILES_DIR,
            destination / "files",
            dirs_exist_ok=True,
        )

    print(
        "Backup criado em:"
    )
    print(
        destination
    )

    return 0


def locations():
    configure_environment()

    print(
        "Dados do servidor de casa:"
    )
    print(
        USER_ROOT
    )
    print()
    print(
        "Banco:"
    )
    print(
        DB_PATH
    )
    print()
    print(
        "Arquivos:"
    )
    print(
        FILES_DIR
    )
    print()
    print(
        "Backups:"
    )
    print(
        BACKUPS_DIR
    )

    return 0


def doctor():
    configure_environment()

    print("=" * 64)
    print("DIAGNÓSTICO - SYSTEM PROJ V6.3 CASA")
    print("=" * 64)
    print()
    print(
        "Python:",
        sys.version.replace(
            "\n",
            " ",
        ),
    )
    print(
        "Executável:",
        sys.executable,
    )
    print(
        "Usuário:",
        getpass.getuser(),
    )

    if sys.version_info < (
        3,
        11,
    ):
        print(
            "[ERRO] Python 3.11 ou superior é necessário."
        )
        return 2

    add_server_path()

    try:
        from app.database import Base, engine
        Base.metadata.create_all(
            bind=engine
        )
        from app.main import app
        print(
            "[OK] API carregada."
        )
    except Exception as exc:
        print(
            "[ERRO] API:",
            exc,
        )
        return 3

    print(
        "[OK] Banco SQLite."
    )

    print(
        "[OK] Pasta de arquivos."
    )

    if CLOUDFLARED.exists():
        print(
            "[OK] cloudflared encontrado."
        )
    else:
        print(
            "[INFO] cloudflared ainda não baixado."
        )

    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=[
            "server",
            "external",
            "download-cloudflared",
            "backup",
            "locations",
            "doctor",
        ],
    )
    args = parser.parse_args()

    commands = {
        "server": server,
        "external": external,
        "download-cloudflared": download_cloudflared,
        "backup": backup,
        "locations": locations,
        "doctor": doctor,
    }

    result = commands[
        args.command
    ]()

    if isinstance(
        result,
        int,
    ):
        raise SystemExit(
            result
        )


if __name__ == "__main__":
    main()
