from __future__ import annotations

import argparse
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


APP_VERSION = "6.4.0"


def runtime_root() -> Path:
    """
    Pasta interna do PyInstaller quando empacotado.
    Durante desenvolvimento usa a própria pasta do arquivo.
    """
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent


BUNDLE_ROOT = runtime_root()

if getattr(sys, "frozen", False):
    SERVER_DIR = BUNDLE_ROOT
else:
    SERVER_DIR = BUNDLE_ROOT / "server"

LOCALAPPDATA = os.environ.get("LOCALAPPDATA")
if LOCALAPPDATA:
    USER_ROOT = Path(LOCALAPPDATA) / "SYSTEM_PROJ_V6_HOME_SERVER"
else:
    USER_ROOT = Path.home() / "SYSTEM_PROJ_V6_HOME_SERVER"

DATA_DIR = USER_ROOT / "data"
FILES_DIR = USER_ROOT / "files"
BACKUPS_DIR = USER_ROOT / "backups"
TOOLS_DIR = USER_ROOT / "tools"
DB_PATH = DATA_DIR / "system_proj_v6_home.db"
SECRET_PATH = DATA_DIR / ".jwt_secret"
URL_FILE = USER_ROOT / "URL_ACESSO_EMPRESA.txt"
CLOUDFLARED = TOOLS_DIR / "cloudflared.exe"


def ensure_dirs():
    for path in (
        USER_ROOT,
        DATA_DIR,
        FILES_DIR,
        BACKUPS_DIR,
        TOOLS_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)


def ensure_secret() -> str:
    ensure_dirs()

    if SECRET_PATH.exists():
        value = SECRET_PATH.read_text(encoding="utf-8").strip()
        if len(value) >= 32:
            return value

    value = secrets.token_urlsafe(48)
    SECRET_PATH.write_text(value, encoding="utf-8")
    return value


def configure_environment():
    ensure_dirs()

    os.environ["APP_NAME"] = "SYSTEM PROJ"
    os.environ["ENV"] = "home-remote-test"
    os.environ["DOMAIN"] = "127.0.0.1"
    os.environ["DATABASE_URL"] = (
        "sqlite:///" + DB_PATH.resolve().as_posix()
    )
    os.environ["JWT_SECRET"] = ensure_secret()
    os.environ["ACCESS_TOKEN_MINUTES"] = "60"
    os.environ["REFRESH_TOKEN_DAYS"] = "30"
    os.environ["CORS_ORIGINS"] = "*"
    os.environ["STORAGE_MODE"] = "local"
    os.environ["LOCAL_STORAGE_PATH"] = str(FILES_DIR.resolve())
    os.environ["WEB_BASE_URL"] = "http://127.0.0.1:8000"
    os.environ["SMTP_HOST"] = ""


def add_server_path():
    # No código-fonte, app está em ./server/app.
    # No EXE, PyInstaller empacota "app" diretamente.
    if not getattr(sys, "frozen", False):
        path = str(SERVER_DIR.resolve())
        if path not in sys.path:
            sys.path.insert(0, path)


def backup_if_needed():
    """
    Faz no máximo um backup automático por dia quando o servidor inicia.
    """
    ensure_dirs()

    if not DB_PATH.exists():
        return

    day = time.strftime("%Y%m%d")
    existing = list(BACKUPS_DIR.glob(f"{day}_*"))

    if existing:
        return

    stamp = time.strftime("%Y%m%d_%H%M%S")
    target = BACKUPS_DIR / stamp
    target.mkdir(parents=True, exist_ok=True)

    shutil.copy2(DB_PATH, target / DB_PATH.name)

    if FILES_DIR.exists():
        shutil.copytree(
            FILES_DIR,
            target / "files",
            dirs_exist_ok=True,
        )


def wait_health(timeout=40):
    deadline = time.time() + timeout
    url = "http://127.0.0.1:8000/api/v1/health"

    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)

    return False


def download_cloudflared():
    ensure_dirs()

    if CLOUDFLARED.exists():
        return True

    url = (
        "https://github.com/cloudflare/cloudflared/"
        "releases/latest/download/"
        "cloudflared-windows-amd64.exe"
    )

    print("Baixando Cloudflare Tunnel oficial...")

    try:
        urllib.request.urlretrieve(url, CLOUDFLARED)
        return True
    except Exception as exc:
        print("Não foi possível baixar cloudflared:")
        print(exc)
        return False


def run_api_in_thread():
    configure_environment()
    add_server_path()

    import uvicorn
    from app.main import app

    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
        access_log=False,
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(
        target=server.run,
        daemon=True,
        name="system-proj-api",
    )
    thread.start()
    return server, thread


def show_header():
    print("=" * 68)
    print(f"SYSTEM PROJ V{APP_VERSION} - SERVIDOR DE CASA")
    print("=" * 68)
    print()
    print("Banco:", DB_PATH)
    print("Documentos:", FILES_DIR)
    print("Backups:", BACKUPS_DIR)
    print()


def run_local():
    configure_environment()
    backup_if_needed()
    show_header()

    server, thread = run_api_in_thread()

    if not wait_health():
        print("ERRO: servidor local não respondeu.")
        return 2

    print("Servidor local funcionando:")
    print("http://127.0.0.1:8000")
    print()
    print("Feche esta janela para encerrar.")

    webbrowser.open("http://127.0.0.1:8000")

    try:
        while thread.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        server.should_exit = True

    return 0


def run_public():
    configure_environment()
    backup_if_needed()
    show_header()

    if not download_cloudflared():
        return 3

    server, thread = run_api_in_thread()

    if not wait_health():
        print("ERRO: servidor local não respondeu.")
        return 4

    print("Servidor local OK.")
    print("Abrindo túnel HTTPS para acesso externo...")
    print()

    tunnel = subprocess.Popen(
        [
            str(CLOUDFLARED),
            "tunnel",
            "--url",
            "http://127.0.0.1:8000",
            "--no-autoupdate",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    public_url = None

    try:
        assert tunnel.stdout is not None

        for line in tunnel.stdout:
            print(line, end="")

            match = re.search(
                r"https://[a-zA-Z0-9-]+\.trycloudflare\.com",
                line,
            )

            if match and public_url is None:
                public_url = match.group(0)
                URL_FILE.write_text(
                    public_url + "\n",
                    encoding="utf-8",
                )

                print()
                print("=" * 68)
                print("LINK PARA USAR NO PC DA EMPRESA")
                print(public_url)
                print("=" * 68)
                print()
                print("O link foi salvo em:")
                print(URL_FILE)
                print()
                print(
                    "IMPORTANTE: o PC de casa precisa permanecer ligado "
                    "e esta janela aberta."
                )
                print(
                    "O Quick Tunnel é temporário; se reiniciar, o endereço "
                    "pode mudar."
                )
                print()

    except KeyboardInterrupt:
        pass
    finally:
        try:
            tunnel.terminate()
        except Exception:
            pass
        server.should_exit = True

    return 0


def diagnose():
    configure_environment()
    add_server_path()
    show_header()

    try:
        from app.database import Base, engine
        Base.metadata.create_all(bind=engine)
        from app.main import app  # noqa
    except Exception as exc:
        print("ERRO ao carregar API:")
        print(exc)
        return 2

    print("API: OK")
    print("SQLite: OK")
    print("Armazenamento local: OK")
    print("Versão:", APP_VERSION)
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--local",
        action="store_true",
        help="Executa somente em localhost, sem acesso externo.",
    )
    parser.add_argument(
        "--diagnostico",
        action="store_true",
    )
    args = parser.parse_args()

    if args.diagnostico:
        code = diagnose()
    elif args.local:
        code = run_local()
    else:
        code = run_public()

    raise SystemExit(code)


if __name__ == "__main__":
    main()
