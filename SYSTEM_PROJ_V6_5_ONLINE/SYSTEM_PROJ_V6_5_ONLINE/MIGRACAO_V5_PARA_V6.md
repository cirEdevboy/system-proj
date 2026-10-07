# Migração V5 → V6.1

A migração foi preparada para ser feita primeiro no ambiente LOCAL.

## O que é preservado

- Usuários/identidades da V5
- Projetos ativos
- Projetos excluídos logicamente
- Cliente, OS, projeto e responsável
- Autor do projeto quando o histórico da V5 permite identificar
- Status atual
- Situação do container
- Etapa de transporte
- Transferência solicitada
- Previsão de coleta
- Consumíveis coletados
- Catálogo de materiais
- Itens dos projetos
- Romaneio
- Histórico da V5 em auditoria
- Datas conhecidas de etapas
- Documentos fiscais/do projeto, quando os arquivos forem fornecidos
- Planilhas antigas de transferência, quando os arquivos forem fornecidos

## O que NÃO pode ser migrado diretamente

A V5 não possuía e-mail, crachá e senha V6 completos para todos os usuários.
Senha também nunca deve ser inventada ou recuperada.

A V6.1 preserva a identidade do usuário para não perder autoria e responsabilidade.
Depois o colaborador usa a opção **Conta migrada** e informa:

- usuário da V5;
- código de ativação;
- nome completo;
- e-mail;
- crachá;
- nova senha.

Depois disso a conta fica `PENDING` e o ADMIN aprova normalmente.

## Passo a passo local

### 1. Instale/abra o Docker Desktop

O teste local usa:
- PostgreSQL
- MinIO
- FastAPI

### 2. Inicie a V6.1

Execute:

`TESTAR_LOCALMENTE.bat`

### 3. Crie seu ADMIN da V6

Execute:

`CRIAR_ADMIN_LOCAL.bat`

Recomendação: use o **mesmo username da sua V5**.
Assim, quando migrar, seus projetos serão vinculados diretamente à sua nova conta V6.

### 4. Copie os dados REAIS da V5

Não mexa nos originais.

Copie para:

`migration_data\gestao_projetos.db`

Se quiser migrar também os arquivos:

`migration_data\DOCUMENTOS_PROJETOS\`

`migration_data\TRANSFERENCIAS_GERADAS\`

### 5. Execute a migração

`MIGRAR_V5_PARA_V6.bat`

Primeiro ele executa uma análise sem gravar dados.
Depois pede confirmação para a migração real.

### 6. Confira o relatório

`migration_data\relatorio_migracao.json`

Ele mostra:
- quantidade migrada;
- documentos que não foram encontrados;
- códigos de material ambíguos;
- usuários criados/reutilizados.

### 7. Usuários antigos

Para usuários V5 que ainda não existiam na V6 é criado:

`migration_data\codigos_ativacao_usuarios.csv`

O ADMIN entrega individualmente o código correspondente à pessoa.

Na tela de acesso ela escolhe:

`Conta migrada`

e completa o cadastro.

## Segurança

O CSV de códigos de ativação contém códigos temporários.
Não deixe esse arquivo em pasta pública depois de distribuir os códigos.

## Migração idempotente

O script calcula SHA-256 do banco V5.
Se você tentar migrar exatamente o mesmo banco uma segunda vez, ele bloqueia para evitar duplicações.

## Depois do teste

Quando você validar que:
- projetos estão corretos;
- documentos abriram;
- catálogo está correto;
- responsáveis estão corretos;
- romaneio está correto;

a mesma migração poderá ser executada no servidor online definitivo.
