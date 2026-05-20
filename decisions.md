# Decisões de Stack

Oito decisões técnicas que definem este repositório e a justificativa de cada uma.

## 1. Python 3.12 como runtime

Fixado em `.python-version` e exigido em `pyproject.toml` (`requires-python = ">=3.12"`).

**Por quê:** versão estável amplamente suportada por ferramentas, SDKs e GitHub Actions runners. Traz `type`-aliases (PEP 695), melhorias de performance em `asyncio` e mensagens de erro mais úteis — suficiente para experimentos com LLMs sem entrar em território instável.

**Decisão prévia revertida:** inicialmente o repo foi configurado em **Python 3.14**. Foi revertido para 3.12 porque parte do ecossistema (algumas extensões nativas e ferramentas auxiliares) ainda não tem wheels estáveis para 3.14, o que aumenta atrito a cada `uv sync` e exige fallback para builds locais. Em um repo de estudo, a fricção operacional importa mais do que recursos de linguagem novos.

## 2. uv como gerenciador de pacotes e ambiente

Substitui pip + venv + pip-tools por um único binário.

**Por quê:** resolução e instalação ordens de magnitude mais rápidas (escrito em Rust), lockfile determinístico (`uv.lock`) versionado, suporte nativo a `dependency-groups` do PEP 735 (separa `dev` de runtime sem extras hacks) e gerencia também a versão do Python. Para um repo onde recrio ambientes com frequência, a velocidade importa.

## 3. ruff em modo estrito para lint e formatação

Único binário substitui flake8, isort, black, pyupgrade, bandit e outros.

**Por quê:** configurado com `select = ["ALL"]` (apenas categorias incompatíveis com scripts de estudo ignoradas), `target-version = "py312"`. Modo estrito força código idiomático desde o começo — para um repo de aprendizado, é melhor ser corrigido cedo do que repetir hábitos ruins. Sendo escrito em Rust, roda em milissegundos, então o atrito é baixo.

## 4. mypy em modo estrito para checagem de tipos

`strict = true` ativado, sem `Any` implícito, sem definições não tipadas.

**Por quê:** SDKs de LLM lidam com payloads complexos (mensagens, tool calls, streaming) e tipagem rigorosa é o que evita confusão sobre formato de resposta. Em modo estrito, mypy obriga anotar tudo e captura erros que passariam silenciosamente. Como é estudo, vale o custo extra de digitar tipos para construir o hábito.

## 5. pre-commit como porteiro de qualidade

Hooks rodam `ruff check --fix`, `ruff format` e `mypy` antes de cada commit.

**Por quê:** garante que nenhum commit entra no histórico violando as regras dos itens 3 e 4 — não depende de lembrar de rodar os checks manualmente. Evita que o repo acumule dívida de lint/tipos. Instalado uma vez com `uv run pre-commit install` e segue automático.

## 6. Layout `src/` por tópico + `.env` para segredos

Cada experimento vive em `src/<tópico>/` (ex.: `src/hello_world/`); chaves de API ficam em `.env` gitignorado, carregadas com `python-dotenv`.

**Por quê:** o repo é coleção de experimentos, não aplicação única — separar por pasta deixa cada estudo isolado e descartável sem acoplamento. `.env` + `python-dotenv` mantém `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `LANGSMITH_API_KEY` fora do controle de versão, com `.env.example` documentando quais variáveis são esperadas.

## 7. Anthropic (Claude) como provider principal de LLM

O SDK `anthropic` é o foco do estudo; `openai` permanece como provider secundário para comparação.

**Por quê:** o objetivo do repo é aprofundar em engenharia de IA, e a Anthropic publica a documentação mais densa sobre os fundamentos práticos (prompt caching, tool use, extended thinking, citations, agentes). Os modelos Claude 4.x (Opus 4.7, Sonnet 4.6, Haiku 4.5) cobrem o espectro de custo/latência/capacidade necessário para experimentos. OpenAI fica para benchmarks lado-a-lado e para entender as diferenças de API entre os dois provedores principais — não para ser o caminho padrão.

## 8. pgvector como vector store padrão

Extensão `vector` do Postgres acessada via `pgvector` + `psycopg` (ver `src/hello_world/pgvector_hello.py`).

**Por quê:** experimentos com embeddings precisam de um lugar para armazenar e consultar vetores por similaridade, e adicionar um banco vetorial dedicado (Pinecone, Weaviate, Qdrant) introduz mais um serviço para subir, autenticar e manter — atrito alto para um repo de estudo. pgvector roda dentro de qualquer Postgres local com `CREATE EXTENSION vector`, oferece os operadores essenciais (`<=>` cosine, `<->` L2, `<#>` inner product) e índices ANN (HNSW, IVFFlat) suficientes para entender os trade-offs de recall/latência sem sair de SQL. Como Postgres já é ferramenta universal, a curva de aprendizado fica no que importa (embeddings e busca vetorial), não em mais uma API proprietária.
