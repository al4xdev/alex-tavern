# Task 19 — Roteiro dos smoke tests que SÓ VOCÊ pode rodar (outcome 6)

É o único item entre a task e o fecho confiante. São 3 ambientes, ~10 min
cada. Em todos: sucesso = a mutação passa COM o app normal; o `curl` externo
sem token toma **403**. Qualquer resultado diferente: anota o passo e o corpo
da resposta e me traz — eu ajusto.

## 1. Desktop (served same-origin, BASE_URL='')

1. `uv run python -m src.main` e abre `http://127.0.0.1:8889` no navegador.
2. Cria uma sessão, manda 1 turno com fala, 1 undo. → Tudo deve funcionar
   (o frontend busca `/bootstrap` e manda `X-Tavern-Token` em toda mutação).
3. Prova negativa, no terminal:
   `curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:8889/session/qualquer/turn -H "Content-Type: application/json" -d '{"speech":"x"}'`
   → esperado **403** (sem token).
4. Reinicia o servidor com a aba aberta e manda outro turno → deve se
   recuperar sozinho (retry do 403 rebusca `/bootstrap`), sem F5.

## 2. Docker (acesso via IP da LAN)

1. Sobe o container e acessa `http://<ip-da-maquina>:8889` de OUTRO
   dispositivo da LAN.
2. Cria sessão + 1 turno. → Deve funcionar pelo caminho same-origin
   (Origin == Host); o token vem junto.
3. Se o provider é llama local com service name do compose (ex.:
   `http://llama:8080`): confirma que o boot NÃO rejeita o api_base
   (single-label é permitido pela política).
4. Prova negativa: mesmo curl do item 1.3 apontando pro IP da LAN → **403**.

## 3. Android / WebView

Aqui existe uma bifurcação que EU não consigo ver daqui — preciso que você
me diga qual dos dois o app usa:

- **(A) WebView carrega o app de `http://127.0.0.1:8889`** (same-origin):
  deve funcionar tudo, igual ao desktop. Só testar sessão + turno.
- **(B) WebView carrega de `file://`** (Origin `null`): `null` está FORA do
  CORS de propósito (roubo de token). O `/bootstrap` só responde se o WebView
  estiver em modo universal-access. Testar: se o app não consegue nem criar
  sessão, é este caso — me diz e eu te passo o ajuste no lado Android
  (servir same-origin é o caminho recomendado; isentar CORS no WebView é o
  plano B).

## Quando terminar

Me manda por ambiente: passou/não passou + (se falhou) passo e resposta.
3/3 verdes → eu fecho a 19 com confiança e migro pra `closed/`.
