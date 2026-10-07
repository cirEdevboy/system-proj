# SYSTEM PROJ V6.2 — TESTE CORPORATIVO SEM DOCKER

Esta edição foi feita para testar a V6 em um computador corporativo
quando o usuário não possui permissão de administrador.

## O que esta edição NÃO usa

- Docker
- PostgreSQL
- MinIO
- serviço do Windows
- alteração de firewall
- porta exposta na rede
- instalação global de pacotes

## Como funciona

Navegador -> FastAPI local -> SQLite V6 -> pasta local de documentos.

O servidor escuta SOMENTE:

`127.0.0.1:8000`

Portanto outros computadores não conseguem acessar este teste e nenhuma
regra de firewall precisa ser criada.

## Onde ficam os dados

Por padrão:

`%LOCALAPPDATA%\SYSTEM_PROJ_V6_TEST`

Dentro desta pasta ficam:

- `data\system_proj_v6_corporativo.db`
- `files\`
- `backups\`
- chave local de autenticação

A pasta do código pode ser apagada/recolocada sem apagar os dados,
desde que `%LOCALAPPDATA%\SYSTEM_PROJ_V6_TEST` seja preservado.

## Passo 1 — verificar Python

O PC precisa ter Python 3.11 ou superior disponível para o seu usuário.

Você pode testar no Prompt de Comando:

`python --version`

ou:

`py -3.11 --version`

Se não houver Python e a política corporativa impedir a instalação,
não tente contornar a segurança da empresa. O próximo caminho será
gerar um pacote portátil no PC pessoal e validar com a TI.

## Passo 2 — preparar sem administrador

Execute:

`PREPARAR_PC_CORPORATIVO.bat`

Ele cria:

`.venv_corporativo`

dentro da pasta do SYSTEM PROJ e instala as dependências somente ali.

Isso normalmente não solicita credenciais de administrador.

Se a empresa bloquear o acesso ao PyPI/proxy, a instalação pode falhar.
Nesse caso envie o erro exibido na janela.

## Passo 3 — iniciar

Execute:

`INICIAR_TESTE_CORPORATIVO.bat`

O navegador abre em:

`http://127.0.0.1:8000`

Uma faixa amarela identifica que você está usando dados locais de teste.

## Passo 4 — criar o ADMIN

Execute:

`CRIAR_ADMIN_CORPORATIVO.bat`

Se você for migrar a V5, use o mesmo username da sua conta antiga.

## Passo 5 — migrar uma CÓPIA da V5

Copie:

`gestao_projetos.db`

para:

`migration_data\gestao_projetos.db`

Opcionalmente copie:

`migration_data\DOCUMENTOS_PROJETOS\`

`migration_data\TRANSFERENCIAS_GERADAS\`

Depois execute:

`MIGRAR_V5_CORPORATIVO.bat`

O processo primeiro faz uma análise, pede confirmação e cria um backup
automático do banco V6 antes da migração real.

## Backup

Execute:

`BACKUP_TESTE_CORPORATIVO.bat`

## Interface Desktop

Para o primeiro teste, use o navegador porque exige menos componentes.

Se o teste web estiver funcionando, opcionalmente execute:

`PREPARAR_DESKTOP_OPCIONAL.bat`

e depois:

`INICIAR_DESKTOP_CORPORATIVO.bat`

PySide6 é grande e pode ser bloqueado por proxy corporativo; a falha do
Desktop não impede o teste pelo navegador.

## Segurança e limitações

Esta edição é somente para validação funcional.

- banco SQLite local;
- um computador;
- sem HTTPS;
- sem compartilhamento de rede;
- sem servidor 24h;
- sem exposição à internet.

Não use este modo como implantação definitiva para vários colaboradores.

A versão definitiva continuará com:
FastAPI + PostgreSQL + armazenamento de arquivos + HTTPS + WebSocket.

## Quando você for para casa

Não será necessário recomeçar o desenvolvimento.

A mesma base V6 será usada para:
1. validar as melhorias;
2. configurar servidor online;
3. migrar os dados aprovados;
4. gerar o cliente/instalador corporativo;
5. deixar o PC da empresa apenas como cliente.
