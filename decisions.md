# Decisões de Stack

Seis decisões técnicas que definem este repositório e a justificativa de cada uma.

## 1. Python 3.14 como runtime

Fixado em `.python-version` e exigido em `pyproject.toml` (`requires-python = ">=3.14"`).

**Por quê:** é a versão estável mais recente no momento da criação do repo, traz melhorias significativas no sistema de tipos (PEP 695, `TypeIs`) e no interpretador (subinterpretadores, JIT experimental). Como o repo é de estudo, faz sentido aprender já com a versão moderna em vez de carregar workarounds de versões antigas.

## 2. uv como gerenciador de pacotes e ambiente

Substitui pip + venv + pip-tools por um único binário.

**Por quê:** resolução e instalação ordens de magnitude mais rápidas (escrito em Rust), lockfile determinístico (`uv.lock`) versionado, suporte nativo a `dependency-groups` do PEP 735 (separa `dev` de runtime sem extras hacks) e gerencia também a versão do Python. Para um repo onde recrio ambientes com frequência, a velocidade importa.

## 3. ruff em modo estrito para lint e formatação

Único binário substitui flake8, isort, black, pyupgrade, bandit e outros.

**Por quê:** configurado com seleção ampla de regras (`ALL` menos algumas categorias incompatíveis com código de estudo), `target-version = "py314"`. Modo estrito força código idiomático desde o começo — para um repo de aprendizado, é melhor ser corrigido cedo do que repetir hábitos ruins. Sendo escrito em Rust, roda em milissegundos, então o atrito é baixo.

## 4. mypy em modo estrito para checagem de tipos

`strict = true` ativado, sem `Any` implícito, sem definições não tipadas.

**Por quê:** SDKs de LLM lidam com payloads complexos (mensagens, tool calls, streaming) e tipagem rigorosa é o que evita confusão sobre formato de resposta. Em modo estrito, mypy obriga anotar tudo e captura erros que passariam silenciosamente. Como é estudo, vale o custo extra de digitar tipos para construir o hábito.

## 5. pre-commit como porteiro de qualidade

Hooks rodam `ruff check --fix`, `ruff format` e `mypy` antes de cada commit.

**Por quê:** garante que nenhum commit entra no histórico violando as regras dos itens 3 e 4 — não depende de lembrar de rodar os checks manualmente. Evita que o repo acumule dívida de lint/tipos. Instalado uma vez com `uv run pre-commit install` e segue automático.

## 6. Layout `src/` por tópico + `.env` para segredos

Cada experimento vive em `src/<tópico>/` (ex.: `src/hello_world/`); chaves de API ficam em `.env` gitignorado, carregadas com `python-dotenv`.

**Por quê:** o repo é coleção de experimentos, não aplicação única — separar por pasta deixa cada estudo isolado e descartável sem acoplamento. `.env` + `python-dotenv` mantém `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` fora do controle de versão, com `.env.example` documentando quais variáveis são esperadas.
