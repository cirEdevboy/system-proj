# SYSTEM PROJ V6.4 — EXECUTÁVEIS + DADOS COMPARTILHADOS

## O modelo recomendado agora

### PC de casa

Use:

`SYSTEM_PROJ_SERVIDOR.exe`

Ele mantém:
- API FastAPI;
- banco SQLite de teste;
- documentos;
- usuários;
- projetos;
- romaneios;
- catálogo;
- histórico;
- notificações;
- acesso HTTPS via Cloudflare Tunnel.

Os dados NÃO ficam ao lado do EXE.

Ficam em:

`%LOCALAPPDATA%\SYSTEM_PROJ_V6_HOME_SERVER`

Isso permite que o executável continue sendo um único arquivo visível.

### PC da empresa

Leve somente:

`SYSTEM_PROJ.exe`

O cliente não possui banco de projetos.

Ele conecta no servidor do PC de casa e usa os mesmos:
- usuários;
- projetos;
- materiais;
- documentos;
- romaneios;
- histórico;
- status.

A configuração do endereço é salva em:

`%APPDATA%\SYSTEM_PROJ\config.json`

Portanto o usuário manipula somente o EXE, embora o Windows naturalmente
mantenha pequenas configurações internas no perfil do usuário.

## Como gerar os dois EXEs

No PC de casa execute:

`GERAR_EXECUTAVEIS_WINDOWS.bat`

O resultado ficará em:

`DIST_FINAL\`

com:

`SYSTEM_PROJ.exe`

`SYSTEM_PROJ_SERVIDOR.exe`

O build precisa ser feito no Windows. PyInstaller não gera de forma
confiável um executável Windows a partir de Linux/macOS.

## Como usar depois do build

### Casa

Execute:

`SYSTEM_PROJ_SERVIDOR.exe`

Por padrão ele:
1. abre a API local;
2. faz backup diário ao iniciar;
3. baixa `cloudflared.exe` para AppData na primeira utilização;
4. cria um Quick Tunnel HTTPS;
5. mostra o link `https://....trycloudflare.com`;
6. grava o link em:

`%LOCALAPPDATA%\SYSTEM_PROJ_V6_HOME_SERVER\URL_ACESSO_EMPRESA.txt`

Mantenha o PC ligado e a janela aberta.

### Empresa

Copie apenas:

`SYSTEM_PROJ.exe`

Dê dois cliques.

Na tela inicial:
1. `Configurar servidor`;
2. cole o link HTTPS exibido no PC de casa;
3. clique `Testar conexão`;
4. faça login.

## Solicitação de transferência

No Desktop:

`Consumíveis / Transferência`

`GERAR E ABRIR NO OUTLOOK`

O cliente:
- solicita ao servidor a geração do XLSX;
- baixa o arquivo temporariamente;
- abre o Outlook Desktop;
- preenche os quatro destinatários padrão;
- preenche assunto;
- preenche corpo;
- anexa XLSX;
- mantém a assinatura padrão já carregada pelo Outlook;
- NÃO envia automaticamente.

O usuário envia manualmente e confirma o envio no SYSTEM PROJ.

## "Sem pasta de arquivos"

No PC da empresa, sim: a distribuição pode ser somente `SYSTEM_PROJ.exe`.

Porém qualquer aplicação precisa guardar algumas informações em algum lugar.
A V6.4 usa AppData/Temp do próprio Windows, e não cria uma pasta do SYSTEM
PROJ ao lado do executável.

No PC de casa, o servidor também é um único EXE visível, mas o banco e os
documentos ficam em AppData, pois precisam sobreviver às atualizações do EXE.

## Limitação atual do Quick Tunnel

O link `trycloudflare.com` pode mudar quando o túnel reinicia.

Se mudar, abra `SYSTEM_PROJ.exe` no trabalho, clique `Configurar servidor`
e cole o novo endereço.

Depois da validação, o próximo passo ideal é configurar um endereço fixo
ou hospedar o backend 24h. Isso elimina a necessidade de atualizar o link.

## Política corporativa

Um EXE PyInstaller normalmente não exige instalação nem administrador.
Entretanto, políticas de AppLocker, SmartScreen, antivírus ou EDR da empresa
podem bloquear executáveis não assinados. Nesse caso a solução correta é
validar/assinar o executável com a TI, e não tentar contornar a política.
