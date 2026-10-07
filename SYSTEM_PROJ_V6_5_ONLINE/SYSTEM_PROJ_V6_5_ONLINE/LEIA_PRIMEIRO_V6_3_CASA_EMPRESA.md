# SYSTEM PROJ V6.3 — CASA + EMPRESA

## Objetivo desta versão

Rodar o servidor no PC de casa e acessar o mesmo SYSTEM PROJ no PC da empresa.

Para este teste usamos:

PC CASA
- FastAPI
- SQLite
- arquivos locais
- Cloudflare Quick Tunnel

PC EMPRESA
- navegador, ou
- cliente Desktop PySide6

O PC de casa precisa permanecer ligado para o PC da empresa acessar.

## Acesso externo sem abrir porta do roteador

Execute no PC de casa:

1. `PREPARAR_SERVIDOR_CASA.bat`
2. `INICIAR_CASA_COM_ACESSO_EMPRESA.bat`

Será criado um endereço parecido com:

`https://nome-aleatorio.trycloudflare.com`

O mesmo endereço fica salvo em:

`URL_ACESSO_EMPRESA.txt`

Abra esse link no navegador do PC da empresa.

O Quick Tunnel é para teste e desenvolvimento. O endereço muda quando
o túnel é reiniciado. Depois da validação vamos trocar por um túnel
fixo/domínio ou hospedagem permanente.

## Solicitação de transferência corrigida

O checkbox manual "Transferência solicitada" foi removido.

Agora:

1. Abra a OS.
2. Vá para `Consumíveis / Transferência`.
3. Confira itens transferíveis e itens em revisão.
4. Clique `GERAR E ABRIR NO OUTLOOK`.
5. O servidor gera e versiona o XLSX.
6. O cliente Desktop baixa o XLSX no PC do colaborador.
7. O Outlook Desktop abre um rascunho com:
   - nnicole@weg.net
   - robertoa@weg.net
   - luanderson@weg.net
   - adrianosena@weg.net
   - assunto preenchido
   - corpo preenchido
   - XLSX anexado
   - assinatura padrão do Outlook preservada
8. O usuário confere e clica ENVIAR no Outlook.
9. Depois confirma no SYSTEM PROJ.

O SYSTEM PROJ nunca aperta "Enviar" automaticamente.

## Navegador x Desktop

Pelo navegador:
- todos os dados do sistema funcionam remotamente;
- a planilha pode ser gerada e baixada;
- o cliente de e-mail pode ser aberto com destinatários/corpo;
- navegadores não permitem anexar automaticamente um arquivo local ao Outlook.

Pelo Desktop:
- o XLSX é baixado;
- o Outlook é automatizado localmente;
- anexo e assinatura são mantidos automaticamente.

Por isso, no PC da empresa, use o pacote `CLIENTE_EMPRESA` para o fluxo
completo de transferência.

## Dados do servidor de casa

Por padrão:

`%LOCALAPPDATA%\SYSTEM_PROJ_V6_HOME_SERVER`

Contém:
- banco SQLite;
- documentos;
- backups;
- chave JWT.

## Segurança

O acesso externo usa HTTPS pelo Cloudflare Tunnel e o SYSTEM PROJ exige login.

Esta arquitetura é adequada para teste. Para uso definitivo com vários
colaboradores, a próxima etapa continua sendo PostgreSQL + servidor online
24h + armazenamento central + túnel/domínio estável.
