# SYSTEM PROJ V6.2.1 — correção da tela inicial

## Erro corrigido

Ao abrir `http://127.0.0.1:8000`, a V6.2 podia gerar:

`TypeError: unhashable type: 'dict'`

A causa era uma mudança na assinatura de `Jinja2Templates.TemplateResponse`
nas versões atuais de Starlette/FastAPI.

A chamada antiga:

`TemplateResponse("index.html", {"request": request, ...})`

foi substituída pela forma atual e explícita:

`TemplateResponse(request=request, name="index.html", context={...})`

## Se você já preparou a V6.2 no PC corporativo

Não é necessário reinstalar Python nem as dependências.

Você pode substituir somente:

`server\app\main.py`

pelo `main.py` corrigido da V6.2.1.

Depois:
1. feche a janela do servidor antigo;
2. execute novamente `INICIAR_TESTE_CORPORATIVO.bat`;
3. abra `http://127.0.0.1:8000`.

Os dados continuam em:

`%LOCALAPPDATA%\SYSTEM_PROJ_V6_TEST`

Portanto a atualização do código não apaga o banco local.
