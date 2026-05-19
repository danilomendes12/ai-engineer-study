# ai-engineer-study

Repositório pessoal de estudos de engenharia de IA. Contém experimentos auto-contidos
contra SDKs de provedores de LLM (Anthropic Claude, OpenAI), exercícios de prompting,
tokenização com `tiktoken` e observabilidade com LangSmith.

Cada experimento mora em `src/<tópico>/` (ex.: `src/hello_world/`) e é independente —
não há aplicação única; o objetivo é aprender comparando abordagens, não construir um
produto. `main.py` na raiz serve como entry point de rascunho.

Stack: Python 3.14, [uv](https://docs.astral.sh/uv/) para dependências, [ruff](https://docs.astral.sh/ruff/)
e [mypy](https://mypy.readthedocs.io/) em modo estrito, `pre-commit` rodando os três
em cada commit. As decisões técnicas estão detalhadas em [decisions.md](decisions.md).

## Setup

```bash
uv sync                          # instala dependências
uv run pre-commit install        # ativa hooks de qualidade
cp .env.example .env             # preencha ANTHROPIC_API_KEY / OPENAI_API_KEY
```

## Comandos úteis

```bash
uv run python main.py            # roda o scratch entry point
uv run ruff check --fix          # lint
uv run ruff format               # formatação
uv run mypy src                  # type check
uv run pre-commit run --all-files
```
