# Decisões de Stack

Registro das escolhas técnicas do projeto e o motivo de cada uma.

## Linguagem & runtime

- **Python 3.14** — versão fixada em `.python-version` e exigida em `pyproject.toml` (`requires-python = ">=3.14"`). Última versão estável, traz melhorias de tipagem e performance úteis para experimentos com LLMs.

## Gerenciamento de dependências

- **uv** — gerenciador de pacotes e ambiente virtual. Escolhido pela velocidade (resolução e instalação muito mais rápidas que pip/poetry), lockfile determinístico (`uv.lock`) e suporte nativo a `dependency-groups`. Substitui pip + venv + pip-tools em uma única ferramenta.

## Qualidade de código

- **ruff** — linter e formatador. Um único binário (escrito em Rust) substitui flake8, isort, black e mais. Configurado para `target-version = "py314"`.
- **mypy** — checagem estática de tipos. Garante segurança de tipos nos experimentos; configurado para `python_version = "3.14"`.
- **pre-commit** — executa `ruff check --fix`, `ruff format` e `mypy` automaticamente antes de cada commit, impedindo que código fora do padrão entre no histórico.

## Bibliotecas de aplicação (LLM)

- **anthropic** — SDK oficial para a API da Anthropic (modelos Claude). Foco principal de estudo.
- **openai** — SDK oficial da OpenAI, para comparação e exercícios multi-provedor.
- **tiktoken** — tokenizer da OpenAI, usado para contar/analisar tokens em prompts e respostas.
- **python-dotenv** — carrega variáveis de ambiente de um arquivo `.env` (gitignorado), mantendo chaves de API fora do código e do controle de versão.

## Organização do projeto

- **Layout `src/`** — experimentos ficam em `src/`, agrupados por tópico (um subdiretório por assunto). `main.py` na raiz serve como ponto de entrada de rascunho. Mantém código de estudo isolado e fácil de descartar.
