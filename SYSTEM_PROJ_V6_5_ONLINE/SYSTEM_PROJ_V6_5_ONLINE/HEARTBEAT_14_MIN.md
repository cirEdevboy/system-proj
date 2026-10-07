# Heartbeat de 14 minutos

A V6.5 inclui o módulo:

`server/app/keepalive.py`

Configuração:

`KEEPALIVE_ENABLED`

`KEEPALIVE_INTERVAL_MINUTES`

`KEEPALIVE_URLS`

Exemplo:

`KEEPALIVE_ENABLED=true`

`KEEPALIVE_INTERVAL_MINUTES=14`

`KEEPALIVE_URLS=https://exemplo.com/health,https://outro.com/health`

O código transforma os endereços em uma lista e faz uma requisição GET
sequencial para cada um.

No Render, `RENDER_EXTERNAL_HOSTNAME` é detectado automaticamente e:

`https://<host>/api/v1/health`

é acrescentado ao array se ainda não estiver presente.

O plano pago recomendado não precisa de heartbeat e o render.yaml o deixa
desativado.

O arquivo render.free-test.yaml habilita o heartbeat para testes, mas isso
não é apresentado como garantia de disponibilidade 24h.
