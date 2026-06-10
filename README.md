# ai-engineer-study

Repositório pessoal de estudos de engenharia de IA. Contém experimentos auto-contidos
contra SDKs de provedores de LLM — **Anthropic Claude como foco principal**, OpenAI e
Gemini como referência para comparação — além de exercícios de prompting, tokenização com
`tiktoken` e observabilidade com LangSmith.

Cada experimento mora em `src/<tópico>/` (ex.: `src/hello_world/`) e é independente —
não há aplicação única; o objetivo é aprender comparando abordagens, não construir um
produto. `main.py` na raiz serve como entry point de rascunho.

Stack: Python 3.12, [uv](https://docs.astral.sh/uv/) para dependências, [ruff](https://docs.astral.sh/ruff/)
e [mypy](https://mypy.readthedocs.io/) em modo estrito, `pre-commit` rodando os três
em cada commit, CI no GitHub Actions executando lint + typecheck a cada push, e pytest
para a suíte de testes. As decisões técnicas estão detalhadas em [decisions.md](decisions.md).

## Setup

```bash
uv sync                          # instala dependências
uv run pre-commit install        # ativa hooks de qualidade
cp .env.example .env             # preencha as chaves (próxima seção)
```

## Chaves de API

Copie `.env.example` para `.env` e preencha:

- `ANTHROPIC_API_KEY` — crie em <https://console.anthropic.com/>.
- `OPENAI_API_KEY` — crie em <https://platform.openai.com/api-keys>.
- `GEMINI_API_KEY` — crie em <https://aistudio.google.com/apikey>.
- `LANGSMITH_API_KEY` — ver seção [Observabilidade com LangSmith](#observabilidade-com-langsmith).

## Comandos úteis

```bash
uv run python main.py            # roda o scratch entry point
uv run uvicorn rest.app:app --reload  # sobe a API REST (porta 8000)
cd dashboard && pnpm dev             # sobe o dashboard (porta 3000)
uv run pytest                    # roda a suíte de testes
uv run ruff check --fix          # lint
uv run ruff format               # formatação
uv run mypy src                  # type check
uv run pre-commit run --all-files
```

## Módulos principais

### `src/llm_calls/` — camada unificada de chamadas LLM

Interface abstrata (`CallLLMFn`) que normaliza chamadas síncronas e streaming para três
provedores — Anthropic, OpenAI e Gemini. Dois pontos de entrada públicos:

```python
from llm_calls import call_llm, stream_llm

result = call_llm("claude-haiku-4-5", "Explique embeddings", 256, "anthropic")
for chunk in stream_llm("gpt-4o-mini", "Explique embeddings", 256, "openai"):
    ...
```

Ambas as funções persistem automaticamente cada chamada no banco SQLite local
(veja `src/db/` abaixo).

### `src/db/` — persistência e analytics

Camada de repositório sobre SQLite (`data/llm_calls.db`):

| Classe | Responsabilidade |
|---|---|
| `LlmCallRepository` | `save`, `get`, `list_all` — CRUD de registros de chamada |
| `LlmCallAnalytics` | `cost_per_call`, `latency_percentiles`, `ttft_percentiles`, `daily_spend` |

```python
from db import LlmCallRepository, LlmCallAnalytics

repo = LlmCallRepository()
analytics = LlmCallAnalytics()

print(analytics.cost_per_call(model="claude-haiku-4-5"))
print(analytics.latency_percentiles())
print(analytics.daily_spend(days=7))
```

### `src/rest/` — API HTTP

API REST construída com [FastAPI](https://fastapi.tiangolo.com/), com schemas Pydantic e documentação interativa automática.

**REST**

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/calls` | Executa uma chamada LLM e persiste o resultado |
| `GET` | `/calls` | Lista chamadas (`?model=`, `?limit=`, `?offset=`) |
| `GET` | `/calls/{id}` | Retorna um registro específico |
| `GET` | `/stats` | Custo, latência (p50/p90/p99), TTFT e gasto diário (`?model=`, `?days=`) |

**WebSocket**

| Rota | Descrição |
|---|---|
| `WS /ws/stream` | Streaming de resposta LLM em tempo real. Envie o mesmo payload `CallRequest` como JSON após conectar; receba chunks `StreamChunk` até `{"type":"done"}`. |

```bash
uv run uvicorn rest.app:app --reload   # sobe o servidor
# acesse http://localhost:8000/docs    # Swagger UI interativo
```

### `dashboard/` — front-end Next.js

Interface web construída com [Next.js 16](https://nextjs.org/), TypeScript, Tailwind CSS
e [shadcn/ui](https://ui.shadcn.com/). Consome exclusivamente o backend FastAPI local —
as chaves de API nunca saem do processo Python.

**Páginas**

| Rota | Descrição |
|---|---|
| `/dashboard` | Cards de custo, latência (p50/p90/p99) e TTFT; gráfico de custo por modelo; tabela paginada de chamadas com painel de detalhes |
| `/playground` | Comparação side-by-side de até 3 modelos: streaming de tokens em tempo real, parâmetros opcionais (`temperature`, `top_p`, `top_k`, `max_tokens`) e métricas por coluna ao finalizar |

**Setup e execução**

```bash
cd dashboard
pnpm install          # instala dependências
pnpm dev              # sobe em http://localhost:3000
```

O backend precisa estar rodando antes: `uv run uvicorn rest.app:app --reload`

O endereço do backend é configurável via `NEXT_PUBLIC_API_BASE` em `dashboard/.env.local`
(padrão: `http://localhost:8000`).

Exemplo REST:

```bash
curl -X POST http://localhost:8000/calls \
  -H "Content-Type: application/json" \
  -d '{"provider":"anthropic","model":"claude-haiku-4-5","message":"Olá!","max_tokens":128}'
```

Exemplo WebSocket (wscat):

```bash
wscat -c ws://localhost:8000/ws/stream
> {"provider":"anthropic","model":"claude-haiku-4-5","message":"Olá!","max_tokens":128}
< {"type":"text","text":"Olá! ..."}
< {"type":"done", ...}
```

### `tests/`

- `tests/db/test_analytics.py` — testes unitários de todos os métodos de analytics com
  banco temporário (`tmp_path`), sem dependência de API.
- `tests/test_providers.py` — testes de integração que exercitam `call_llm` e
  `stream_llm` contra os três provedores reais, verificando resposta e persistência.
  Gemini é marcado `xfail` para tolerar erros de cota.

## Observabilidade com LangSmith

[LangSmith](https://smith.langchain.com/) é a plataforma de tracing/observabilidade
da LangChain. Cada chamada a um SDK de LLM instrumentado vira um *trace* com prompts,
respostas, latência, contagem de tokens e custo estimado — útil pra entender o que
está acontecendo dentro de prompts mais elaborados (tool use, multi-turn, chains).

### Setup

1. **Criar conta** em <https://smith.langchain.com/> — o tier gratuito (Developer)
   inclui 5k traces/mês, suficiente para estudo.
2. **Gerar API key** em *Settings → API Keys → Create API Key*.
3. **Preencher no `.env`**:

   ```bash
   LANGSMITH_TRACING=true
   LANGSMITH_API_KEY=ls__...           # cole a key gerada
   LANGSMITH_PROJECT=ai-engineer-study  # nome do projeto que aparece no dashboard
   ```

4. **Carregar o `.env`** no script (já feito via `python-dotenv`). Com
   `LANGSMITH_TRACING=true` no ambiente, o SDK do `langsmith` instala
   automaticamente traços para chamadas Anthropic/OpenAI feitas no mesmo processo.

### Ver os traces

Os traces aparecem em <https://smith.langchain.com/> dentro do projeto
`ai-engineer-study`. Cada execução vira uma linha com inputs, outputs, latência e
tokens. Útil pra diff de prompts: rode duas variantes, abra os dois traces lado a
lado e compare resposta + custo.
