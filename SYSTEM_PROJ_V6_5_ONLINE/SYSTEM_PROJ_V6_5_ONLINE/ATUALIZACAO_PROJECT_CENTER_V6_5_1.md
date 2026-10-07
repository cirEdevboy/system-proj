# Project Center V6.5.1

Atualização focada na interface e no catálogo de insumos.

## Visual
- remove a faixa "MODO DE TESTE CORPORATIVO";
- marca principal alterada para PROJECT CENTER;
- dashboard passa a funcionar como lobby dos projetos;
- indicadores: projetos abertos, transferências pendentes, em logística e sob minha responsabilidade;
- cards de projetos com sinalização visual de status;
- "Materiais" renomeado visualmente para "Banco de insumos";
- executável do cliente passa a ser `PROJECT_CENTER.exe`.

## Importação do banco de insumos
O importador foi refeito para o ambiente Render/PostgreSQL.

Antes, para cada linha do Excel era executada uma consulta no banco.
Em um catálogo com milhares de linhas isso poderia deixar o endpoint muito
lento no plano gratuito.

Agora:
1. Excel é lido em modo econômico;
2. registros são deduplicados em memória;
3. catálogo atual é carregado em uma consulta;
4. novos registros são inseridos em lote pelo SQLAlchemy;
5. existentes são atualizados sem milhares de SELECTs;
6. interface mostra novos, atualizados, ignorados, total ativo e tempo.

Formatos aceitos:
- XLSX
- XLSM

Estrutura histórica suportada:
- Id_Inicial
- Material
- Texto breve de material
- Centro
- Depósito
- UM básica

A planilha `CONSULTA` é priorizada automaticamente.

## Atualização no GitHub atual
Substitua estes arquivos dentro da pasta `SYSTEM_PROJ_V6_5_ONLINE`:

- server/app/main.py
- server/app/config.py
- server/app/services.py
- server/app/templates/index.html
- server/app/static/app.js
- server/app/static/app.css
- desktop/system_proj_client/app.py
- desktop/system_proj_client/outlook.py
- render.free-test.yaml

Depois faça Commit. O Render deve fazer novo deploy automaticamente.
