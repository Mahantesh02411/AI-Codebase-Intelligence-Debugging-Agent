# AI Codebase Intelligence & Debugging Agent

**Neural Storm 2026 · Track 1 Future Tech · FT-05 AI-Powered Automated Code Review**
Team: _add team name_ · Members: Santosh Suresh Madannavar ([@Santosh02411](https://github.com/Santosh02411)) _(add other members)_

## The problem
Reviewing code and chasing bugs eats most of an engineer's week. A reviewer has to find the relevant code across hundreds of files, work out how it is reached, decide whether a change is safe, and then prove a fix works. Chat-with-your-repo tools answer questions but do not *verify* anything, and AI patches that "look right" regularly break something else or just hide the error.

## The solution
An **agentic RAG system** that treats a repository as something to investigate, not something to paste into a prompt:

1. **Index** a repository (GitHub URL, ZIP, local folder) with code-aware parsing (Python `ast`, Tree-sitter for 8 languages) into functions, classes, routes, call graph and import graph.
2. **Investigate** with a LangGraph team of specialists (Planner, Researcher, Debugger, Coder, Tester, Reviewer, Documenter). The model chooses among 18 tools (hybrid code search, symbol lookup, grep, callers/callees, git history, sandboxed tests...) and every claim must cite code it was actually shown.
3. **Review** code and pull requests: deterministic checks first (security, error handling, secrets), then AI findings. Each finding has a severity, a confidence, the offending line as evidence and a concrete fix; duplicates are merged and AI findings that point at code that does not exist are marked low-confidence.
4. **Debug and fix**: decode the error, reproduce it by running tests, find the root cause, write a multi-file patch, and **verify it in an isolated sandbox**. A fix is reported as *resolved* only when a regression test fails before the patch and passes after it. Otherwise the report says *unverified* and why.
5. **Human approval** before anything is applied to the project or sent to GitHub.

### Why it fits FT-05 (automated code review)
The Review mode (`/review`), the PR analysis and review workflow (Analyze PR, Review PR with inline comments anchored to real diff lines, Fix Issue) and the patch reviewer are all modes of the same agent. Findings combine static analyzers (Ruff, Bandit, Semgrep, ESLint and others) with model review grounded in retrieved code and the call graph.

## Architecture
```
 repo (GitHub / ZIP / folder) ─► parse (ast + Tree-sitter) ─► chunks, call graph, import graph ─► embeddings + BM25 (pgvector or in-memory)
                                                                                                   │
 question / error / PR ─► Planner ─► Researcher (model-chosen tools) ─► Debugger ─► Coder ─► Tester (Docker sandbox) ─► Reviewer ─► Documenter
                             ▲            │ hybrid search → RRF → rerank → token-budgeted context with [n] citations      │ failed test
                             └────────────┴──────────────────── reflection / research loops (bounded) ◄─────────────────────┘
 human approval ─► apply patch / open PR
```
Deeper dives: [docs/AGENT.md](docs/AGENT.md) (LLM layer, context building, agent graph) · [docs/RAG.md](docs/RAG.md) (retrieval pipeline, pgvector, metrics) · [docs/SANDBOX.md](docs/SANDBOX.md) (execution trust model) · [docs/BUILD_PLAN.md](docs/BUILD_PLAN.md) (architecture and decisions) · [docs/PROGRESS.md](docs/PROGRESS.md) (what is implemented, tested and validated).

## Core capabilities
| Capability | Endpoint | Notes |
|---|---|---|
| Ask about the code (RAG with citations) | `/chat`, `/search` | `[n]` citations and `file:line` references are validated against what was retrieved |
| Debug an error and propose a verified fix | `/debug` | six-section report; verdict is `resolved`, `partial`, `no_regressions`, `unverified` or `not_resolved` |
| Review code (automatic checks + AI) | `/review` | severity, confidence, evidence, remediation; deduplicated |
| Review / analyse a pull request | GitHub panel | inline comments only on lines in the diff; nothing posted without approval |
| Change code across files, write tests | `/change`, `/generate-tests` | tested before and after in a throw-away copy |
| Code-quality dashboard | `/quality/run` | tests, coverage, Ruff, Pylint, mypy, Bandit, Semgrep, ESLint and more feed one score |
| Architecture overview | `/architecture` | from extracted routes, imports and dependencies |

**Reliability and safety built in:** repository text is treated as untrusted data (prompt-injection patterns are flagged and labelled, secrets are masked before reaching a prompt); symlinks are never followed when indexing or copying; patches that merely swallow exceptions or add `noqa`/`type: ignore` are rejected by deterministic checks; tool failures are reported as failures; runs have step, call and wall-clock limits; all repository code runs in a locked-down Docker container or not at all (fail-closed).

## Technology stack
Python 3.11+ · FastAPI · LangGraph / LangChain core · Gemini or OpenAI behind one interface (plus an offline mock) · PostgreSQL + pgvector (or in-memory) · BM25 + RRF + cross-encoder/heuristic/LLM reranking · Python `ast` + Tree-sitter · Docker sandbox · Next.js, TypeScript, Monaco editor (IDE UI) and a built-in single-page UI.

## Quick start
Keys and tokens (all optional; the app runs offline without them): [docs/ENV_SETUP.md](docs/ENV_SETUP.md) explains how to get each one and what happens if it is missing.
```bash
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # defaults to the offline mock LLM; set LLM_PROVIDER=gemini|openai, the API key and LLM_MODEL for real runs
uvicorn app.main:app --reload   # UI at http://localhost:8000, API docs at /docs
```
**Web app (redesigned):** `uvicorn app.main:app --reload` serves it at http://localhost:8000 (pre-built into `app/webapp`; after changing `frontend/`, run `scripts/build_frontend.sh`, which needs Node 18+). For frontend development with hot reload: `cd frontend && cp .env.example .env.local && npm install && npm run dev` (http://localhost:3000). It has: dashboard, AI chat with a live agent timeline, code explorer, interactive architecture graphs, debugging, review, quality, patches, testing and GitHub pages, in light and dark themes. See [frontend/README.md](frontend/README.md). The previous single-page UI is still available at `/classic`, and the multi-tab IDE layout at `/workbench`.
Code execution needs the sandbox images: `scripts/build_sandbox.sh` (Docker required). Without Docker the agent still answers and reviews, but patches are reported as **unverified** because nothing runs. `SANDBOX_MODE=local` is for your own machine only.
PostgreSQL + pgvector: `docker compose up db` and set `DATABASE_URL`.

```bash
# try it from the command line
curl -X POST localhost:8000/repositories -H 'content-type: application/json' -d '{"source":"https://github.com/<owner>/<repo>"}'
curl -X POST localhost:8000/debug -H 'content-type: application/json' -d '{"repo_id":"<id>","question":"500 error when creating a delivery"}'
```
Patch generation and root-cause analysis need a real LLM; the mock provider only does retrieval-based answers.

## Configuration
All settings are environment variables, documented in [.env.example](.env.example): `LLM_PROVIDER`, `LLM_MODEL`, `LLM_MODEL_FAST`, `EMBEDDING_PROVIDER`, `DATABASE_URL`, `SANDBOX_MODE`, `MAX_LLM_CALLS`, `MAX_AGENT_TOTAL_STEPS`, `MAX_RUN_SECONDS`, `TEST_TIMEOUT`, `GITHUB_TOKEN` and GitHub OAuth settings.

## Strict code review
Open **Code Review**: every analysable file is checked in about a second with real parsers and fixed rules (no model): Python syntax errors, undefined names and misspellings (“did you mean”), `self.` attribute typos, wrong imports between project files, wrong call arguments, unused code, common bugs and security issues; syntax errors (missing/extra braces and brackets) in JS/TS/Java/Go/Rust/C/C++; JSON/YAML/TOML/HTML/CSS structure. The page lists exactly what was and was not analysed. **The review reads the server's copy of your project**: after you edit files in your original folder, use *Sync & review again* (or the project menu → *Sync from source & re-index*). Type checking is not included (use the Code Quality scan for mypy).

## Evaluation (what has actually been measured)
Everything below was produced by this repository's harness (`python -m app.rag.eval`). **No real-LLM or real-embedding results are included yet**; the numbers are offline baselines and must not be read as model quality.

*Retrieval, offline, hashing embedder, 50 questions on this repository, symbol-level labels* ([eval/results/offline_baseline_codebase_agent.md](eval/results/offline_baseline_codebase_agent.md)): the best offline configuration (hash vectors + BM25 hybrid + heuristic rerank) reaches MRR 0.339 and Recall@5 0.420. Hashing embeddings are largely lexical, so this is a floor, not the ceiling; real embedding models are supported (`--embedders openai:...,gemini:...,bge:...`) but have not been run for this report.

*Agent outcomes, offline mock LLM, 4 hand-labelled cases on the small `delivery_sync` fixture* ([eval/results/agent_offline_mock_delivery_sync.md](eval/results/agent_offline_mock_delivery_sync.md)): the expected file was in the agent's context in 4 of 4 cases. Root-cause accuracy, citation validity, patch success and regression-test effectiveness are **not measured** (n/a) because the mock model produces no analysis or patches. They are computed by the same command with a real provider:
```bash
python -m app.rag.eval agent --repo tests/fixtures/delivery_sync --cases eval/datasets/agent_cases_delivery_sync.jsonl --provider gemini
```
Four cases are a smoke test, not a benchmark.

## Tests
```bash
pytest                      # offline: no keys, no network, no Docker (the sandbox is tested with a fake docker); last full run: 480 passed, 38 skipped
```
See [docs/PROGRESS.md](docs/PROGRESS.md) for the current test count and what each layer covers.

## Limitations
- Real-provider quality (patch success, root-cause accuracy) is unmeasured; the prompts were exercised with scripted models.
- Real Docker sandbox runs, real GitHub flows (PR creation, review posting) and interactive browser use of the frontend were not verified end to end.
- Static call-graph resolution is name-based: dynamic dispatch and reflection are only resolved when the name is unique (marked "guessed by name").
- Prompt-injection defence is layered (prompt rules, pattern flagging, human approval, sandbox) but pattern flagging cannot catch every phrasing.
- Secrets are masked in retrieved context and tool results; the exact source shown to the coder for editing is not masked, because edits are matched literally.
- Verification needs runnable tests. Projects without tests get `unverified` verdicts, never a claimed fix.
- One local user: add real accounts before exposing the server on a network.

## AI usage disclosure
This project was built with AI assistance: **Claude (Anthropic)** wrote and reviewed large parts of the code, tests and documentation under the author's direction. At runtime the agent calls an LLM you configure (Gemini or OpenAI) and, optionally, embedding models. Add any other tools used (ChatGPT, GitHub Copilot, Cursor...).

## Pushing to GitHub
`venv/`, `.env` and `data/` are git-ignored. Never commit the virtual environment.
