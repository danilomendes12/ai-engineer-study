# ai-engineer-study

Repositório pessoal de estudos de engenharia de IA. Contém experimentos auto-contidos
contra SDKs de provedores de LLM — **Anthropic Claude como foco principal** e OpenAI
como referência para comparação — além de exercícios de prompting, tokenização com
`tiktoken` e observabilidade com LangSmith.

Cada experimento mora em `src/<tópico>/` (ex.: `src/hello_world/`) e é independente —
não há aplicação única; o objetivo é aprender comparando abordagens, não construir um
produto. `main.py` na raiz serve como entry point de rascunho.

Stack: Python 3.12, [uv](https://docs.astral.sh/uv/) para dependências, [ruff](https://docs.astral.sh/ruff/)
e [mypy](https://mypy.readthedocs.io/) em modo estrito, `pre-commit` rodando os três
em cada commit, e CI no GitHub Actions executando lint + typecheck a cada push. As
decisões técnicas estão detalhadas em [decisions.md](decisions.md).

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
- `LANGSMITH_API_KEY` — ver seção [Observabilidade com LangSmith](#observabilidade-com-langsmith).

## Comandos úteis

```bash
uv run python main.py            # roda o scratch entry point
uv run ruff check --fix          # lint
uv run ruff format               # formatação
uv run mypy src                  # type check
uv run pre-commit run --all-files
```

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
