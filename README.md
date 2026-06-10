# AI Experimentation Dashboard

Dashboard de experimentação e avaliação de modelos de linguagem. Permite comparar
provedores e modelos lado a lado — **Anthropic Claude** como foco principal, com
suporte a OpenAI, Gemini e **Ollama (modelos open-weight locais)** — medindo custo,
latência e qualidade de resposta em tempo real.

## Visão geral

| Camada | Tecnologia | Função |
|---|---|---|
| Backend | Python 3.12 + FastAPI | Chamadas LLM, persistência SQLite, analytics |
| Frontend | Next.js 16 + Tailwind + shadcn/ui | Dashboard e Playground |
| Provedores | Anthropic, OpenAI, Gemini, Ollama | Execução dos modelos |

## Setup rápido

```bash
# backend
uv sync
uv run pre-commit install
cp .env.example .env        # preencha as chaves de API

# frontend
cd dashboard
pnpm install
```

Subir tudo:

```bash
uv run uvicorn rest.app:app --reload   # API em http://localhost:8000
cd dashboard && pnpm dev               # UI em http://localhost:3000
```

## Chaves de API

Copie `.env.example` para `.env` e preencha:

- `ANTHROPIC_API_KEY` — <https://console.anthropic.com/>
- `OPENAI_API_KEY` — <https://platform.openai.com/api-keys>
- `GEMINI_API_KEY` — <https://aistudio.google.com/apikey>
- `LANGSMITH_API_KEY` — ver seção [Observabilidade](#observabilidade-com-langsmith)

## Ollama (modelos locais)

```bash
brew install ollama
ollama pull llama3.2    # ~2 GB
ollama serve
```

Com o servidor rodando, selecione `ollama` como provedor no Playground ou via API.
O endpoint é configurável via `OLLAMA_BASE_URL` (padrão: `http://localhost:11434/v1`).

## Páginas do dashboard

### `/dashboard` — Analytics

Visão consolidada de todas as chamadas realizadas:

- Cards de custo total, latência (p50 / p90 / p99) e TTFT (time-to-first-token)
- Gráfico de custo por modelo
- Tabela paginada de chamadas com painel de detalhes por registro

Filtros disponíveis por modelo (`?model=`) e janela de dias (`?days=`).

### `/playground` — Comparação de modelos

Ambiente de comparação side-by-side de até 3 modelos simultaneamente:

- Prompts de sistema e usuário compartilhados ou individuais por coluna
- Parâmetros opcionais: `temperature`, `top_p`, `top_k`, `max_tokens`
- Streaming de tokens em tempo real via WebSocket
- Métricas de latência, custo e TTFT exibidas ao final de cada resposta

## API REST

```bash
# executar uma chamada e persisti-la
curl -X POST http://localhost:8000/calls \
  -H "Content-Type: application/json" \
  -d '{"provider":"anthropic","model":"claude-haiku-4-5","message":"Olá!","max_tokens":128}'

# listar chamadas
curl http://localhost:8000/calls?limit=20

# estatísticas agregadas
curl http://localhost:8000/stats?days=7
```

Documentação interativa: `http://localhost:8000/docs`

**WebSocket** — streaming em tempo real:

```bash
wscat -c ws://localhost:8000/ws/stream
> {"provider":"anthropic","model":"claude-haiku-4-5","message":"Olá!","max_tokens":128}
< {"type":"text","text":"Olá! ..."}
< {"type":"done", ...}
```

## Comandos úteis

```bash
uv run pytest                      # testes
uv run ruff check --fix            # lint
uv run ruff format                 # formatação
uv run mypy src                    # type check
uv run pre-commit run --all-files  # todos os hooks
```

## Observabilidade com LangSmith

[LangSmith](https://smith.langchain.com/) adiciona tracing automático a cada chamada
de LLM — prompts, respostas, latência, tokens e custo estimado em um único lugar.

```bash
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=ls__...
LANGSMITH_PROJECT=ai-engineer-study
```

Com essas variáveis no `.env`, o SDK instala traços automaticamente. Acesse os
traces em <https://smith.langchain.com/> no projeto `ai-engineer-study`.
