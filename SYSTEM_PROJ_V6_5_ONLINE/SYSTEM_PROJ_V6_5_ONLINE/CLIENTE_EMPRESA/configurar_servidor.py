from pathlib import Path
import json
import os

appdata = Path(
    os.environ.get(
        "APPDATA",
        str(Path.home())
    )
)

config_dir = (
    appdata
    / "SYSTEM_PROJ"
)

config_dir.mkdir(
    parents=True,
    exist_ok=True,
)

url = input(
    "Cole o link HTTPS exibido no PC de casa: "
).strip().rstrip("/")

if not url.startswith(
    (
        "https://",
        "http://",
    )
):
    raise SystemExit(
        "Informe um endereço começando com http:// ou https://"
    )

path = (
    config_dir
    / "config.json"
)

path.write_text(
    json.dumps(
        {
            "server_url": url
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)

print()
print(
    "Servidor configurado:"
)
print(
    url
)
print()
print(
    "Arquivo:"
)
print(
    path
)
