# SYSTEM PROJ V6.5

Arquitetura cliente-servidor para uso corporativo online.

## Componentes

- **Servidor online:** FastAPI + PostgreSQL + WebSocket.
- **Desktop profissional:** PySide6, sem banco local.
- **Web:** interface no navegador servida pelo próprio FastAPI.
- **Documentos:** MinIO/S3 em produção; pasta local em desenvolvimento.
- **HTTPS:** Caddy com certificado automático.
- **Backup:** backup diário do PostgreSQL no Docker Compose.

## Regras principais implementadas

- Todos os projetos são públicos para usuários ativos.
- Somente o responsável atual ou ADMIN pode alterar o projeto.
- Projeto guarda `iniciado por` e `responsável atual`.
- Transferência de responsabilidade exige aceite do novo responsável.
- ADMIN pode assumir/transferir em modo de contingência com motivo auditado.
- Histórico completo de responsáveis.
- Datas automáticas por mudança de etapa.
- Situação do container e etapa de transporte independentes.
- Cadastro no primeiro acesso: nome completo, e-mail, usuário, crachá e senha.
- Senha mínima de 8 caracteres; armazenada somente como hash Argon2id.
- Usuário novo fica `PENDENTE` até aprovação do ADMIN.
- Notificações em tempo real por WebSocket.
- Sessões/dispositivos e encerramento remoto de sessão.
- Auditoria de alterações.
- Documentos com versionamento.
- Busca global.
- Catálogo de materiais central.
- Romaneio XLSX/PDF sem código SAP e sem dados de container/transporte.
- Controle otimista de concorrência por `version` do projeto.
- Exclusão lógica (soft delete).
- API versionada em `/api/v1`.

## Desenvolvimento rápido

1. Copie `.env.example` para `.env` e ajuste `JWT_SECRET`.
2. Rode `docker compose up --build`.
3. Crie o primeiro ADMIN:
   `docker compose exec api python /app/scripts/bootstrap_admin.py`
4. Acesse `http://localhost:8000` em desenvolvimento.

## Produção

Configure no `.env`:

- `DOMAIN=systemproj.suaempresa.com`
- `JWT_SECRET` forte e único
- SMTP corporativo para recuperação de senha
- senhas do PostgreSQL/MinIO

Aponte o DNS do domínio para o servidor e rode `docker compose up -d --build`.
O Caddy publica HTTPS automaticamente.

## Desktop

No diretório `desktop`:

`pip install -r requirements.txt`

`python main.py`

Para gerar EXE:

`build_windows.bat`

Para gerar instalador, abra `installer/SYSTEM_PROJ_V6.iss` no Inno Setup após gerar o EXE.

## Migração da V5

Use `scripts/migrate_v5_sqlite.py`. Usuários migrados sem senha ficam `PENDENTE_RESET`, preservando nome/perfil quando disponível; projetos, materiais, itens, histórico e romaneio são migrados quando as tabelas existirem.

## Observação de segurança

A V6 não distribui credenciais de banco no PC do colaborador. O cliente conhece apenas a URL HTTPS da API. PostgreSQL e armazenamento ficam privados no servidor.


## Migração V5

Consulte `MIGRACAO_V5_PARA_V6.md` e use `MIGRAR_V5_PARA_V6.bat`.


## Teste no PC corporativo sem Docker

Leia `LEIA_PRIMEIRO_PC_CORPORATIVO.md`.


## MASTER ADMIN

Consulte `MASTER_ADMIN_V6_2_2.md`.


## V6.3 Casa + Empresa

Leia `LEIA_PRIMEIRO_V6_3_CASA_EMPRESA.md`.


## V6.4 executáveis

Leia `LEIA_PRIMEIRO_V6_4_EXECUTAVEIS.md`.


## V6.5 Online

Servidor preparado para Render + PostgreSQL + Cloudflare R2.

Leia `DEPLOY_RENDER_R2.md`.
