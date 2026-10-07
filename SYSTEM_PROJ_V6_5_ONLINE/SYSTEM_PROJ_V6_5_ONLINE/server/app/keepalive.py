from __future__ import annotations

import asyncio
import logging

import httpx

from .config import settings


logger = logging.getLogger(
    "system_proj.keepalive"
)


async def ping_url(
    client: httpx.AsyncClient,
    url: str,
):
    try:
        response = await client.get(
            url,
            timeout=12.0,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "SYSTEM-PROJ-Heartbeat/6.5"
                )
            },
        )

        logger.info(
            "Heartbeat %s -> HTTP %s",
            url,
            response.status_code,
        )

    except Exception as exc:
        logger.warning(
            "Heartbeat falhou para %s: %s",
            url,
            exc,
        )


async def keepalive_loop():
    """
    Loop de monitoramento configurável.

    O array de URLs vem de:
        settings.keepalive_url_list

    O intervalo padrão é 14 minutos.

    Observação:
    este mecanismo é útil como heartbeat/monitoramento e para testes.
    Ele não transforma um plano gratuito em uma garantia contratual
    de disponibilidade 24h.
    """
    interval_seconds = max(
        60,
        int(
            settings.keepalive_interval_minutes
        ) * 60,
    )

    # Evita disputar recursos durante o bootstrap.
    await asyncio.sleep(
        30
    )

    while True:
        urls = list(
            settings.keepalive_url_list
        )

        if not urls:
            logger.info(
                "Heartbeat ativo, mas sem URLs configurados."
            )

        async with httpx.AsyncClient() as client:
            for url in urls:
                await ping_url(
                    client,
                    url,
                )

        await asyncio.sleep(
            interval_seconds
        )
