# SYSTEM PROJ V6.5 — RENDER + POSTGRESQL + CLOUDFLARE R2

## Arquitetura

PC empresa / PC casa / navegador
        |
        | HTTPS
        v
Render Web Service (FastAPI)
        |
        +--> Render PostgreSQL
        |
        +--> Cloudflare R2 (documentos)

O computador de casa pode ficar desligado.

## Arquivo de implantação recomendado

Use:

`render.yaml`

Ele cria:
- Web Service pago, sem spin-down por inatividade;
- PostgreSQL pago;
- conexão automática do banco;
- HTTPS do Render;
- health check.

## Arquivo de teste gratuito

Existe também:

`render.free-test.yaml`

Este é SOMENTE para validação.

O código contém um heartbeat configurável:

`KEEPALIVE_ENABLED=true`

`KEEPALIVE_INTERVAL_MINUTES=14`

`KEEPALIVE_URLS=url1,url2,...`

A aplicação converte `KEEPALIVE_URLS` em um array e, no Render, acrescenta
automaticamente o próprio:

`https://<RENDER_EXTERNAL_HOSTNAME>/api/v1/health`

O loop executa aproximadamente a cada 14 minutos enquanto o processo está ativo.

IMPORTANTE: isso NÃO transforma o plano Free em hospedagem 24h garantida.
O próprio Render classifica Free como ambiente de teste, pode reiniciar
instâncias, e o PostgreSQL Free expira.

## Cloudflare R2

Antes do primeiro deploy:

1. Entre no Cloudflare Dashboard.
2. Abra R2 Object Storage.
3. Crie um bucket, por exemplo:

`system-proj`

4. Crie um API Token com Object Read & Write limitado a esse bucket.
5. Guarde:
   - endpoint S3;
   - nome do bucket;
   - Access Key ID;
   - Secret Access Key.

O endpoint é parecido com:

`https://ACCOUNT_ID.r2.cloudflarestorage.com`

## Render

### Opção recomendada

1. Coloque esta pasta em um repositório privado GitHub/GitLab.
2. No Render:
   `New -> Blueprint`
3. Selecione o repositório.
4. O Render detectará `render.yaml`.
5. Durante a criação ele solicitará as variáveis `sync: false`.

Preencha:
- S3_ENDPOINT
- S3_BUCKET
- S3_ACCESS_KEY
- S3_SECRET_KEY
- MASTER_ADMIN_USERNAME
- MASTER_ADMIN_EMAIL
- MASTER_ADMIN_BADGE
- MASTER_ADMIN_FULL_NAME
- MASTER_ADMIN_PASSWORD

A senha do MASTER_ADMIN não fica no código.

## Depois do deploy

O Render fornecerá algo parecido com:

`https://system-proj-api.onrender.com`

Teste:

`https://system-proj-api.onrender.com/api/v1/health`

A resposta deve conter:

`"version": "6.5.0"`

`"database": "postgresql"`

`"storage_mode": "s3"`

## Cliente Windows

Gere o executável no seu Windows usando:

`GERAR_EXECUTAVEIS_WINDOWS.bat`

Leve somente:

`DIST_FINAL\SYSTEM_PROJ.exe`

No PC da empresa:

1. abra SYSTEM_PROJ.exe;
2. clique Configurar servidor;
3. use a URL fixa do Render;
4. clique Testar conexão;
5. faça login.

A partir desse momento o PC de casa não participa do funcionamento.

## Solicitação de transferência

Continua como na V6.4:

- servidor gera XLSX;
- cliente Desktop baixa;
- Outlook Desktop abre localmente;
- destinatários, assunto e corpo são preenchidos;
- XLSX é anexado;
- assinatura do Outlook é preservada;
- o usuário clica em ENVIAR;
- depois confirma no SYSTEM PROJ.

## Migração de dados

A V6.5 usa PostgreSQL.

O script existente:

`scripts/migrate_v5_sqlite.py`

continua disponível.

Para dados corporativos reais, primeiro valide a política de TI sobre
hospedagem externa antes de colocar documentos/projetos de produção na nuvem.
