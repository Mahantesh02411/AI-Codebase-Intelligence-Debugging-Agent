# Progress Tracker

**Current version:** v13 · **Last updated:** 2026-11-04

Legend: **Implemented** = code exists · **Tested** = covered by the offline test suite (scripted LLM, local sandbox, fake docker) · **Validated** = run against a real service (real LLM, real Docker, real GitHub, browser).

## Test status
Offline suite: 480 passed, 38 skipped, 0 failed (32 test files, run in two groups on 2026-11-03 in a sandbox with `coverage` installed). Skips are tests that need optional services or packages missing there (e.g. PostgreSQL). Nothing below is "Validated" unless stated.

## Capability matrix
| Capability | Implemented | Tested offline | Validated with real services |
|---|---|---|---|
| Ingest (GitHub URL, ZIP, folder), incremental indexing, symlinks never followed | yes | yes | git clone path not run here |
| Code intelligence (ast + Tree-sitter ×8, call/import/inheritance graphs, impact) | yes | yes | no |
| Hybrid RAG (vectors + BM25 + RRF + rerank), pgvector store | yes | in-memory yes; pgvector tests skipped here | no |
| LLM layer (OpenAI/Gemini/mock, retries, fallback, JSON repair, tools, usage) | yes | scripted LLM only | **no real-provider run** |
| LangGraph agent, 18 tools, reflection loops, conversation memory | yes | yes | no |
| Debugging report, reproduction, regression-test verification | yes | yes | no |
| Multi-file patch engine, approval, revert, repair | yes | yes | no |
| Docker sandbox, fail-closed | yes | fake docker | **no real Docker run** |
| Quality dashboard (10 analyzers, coverage, score) | yes | yes | tools run in this environment only where installed |
| GitHub OAuth, PR analysis/review, issue fix, PR creation | yes | mocked GitHub | **no real GitHub run** |
| Next.js IDE | yes | API only | **not clicked through in a browser** |
| Evaluation harness (retrieval + agent outcomes) | yes | yes | offline/mock results only |

## Added in v13 (each has regression tests in `tests/test_v13_hardening.py`)
- Review findings: severity, confidence, evidence, remediation; fewer false positives (placeholder secrets, constant `eval`, test fixtures); deduplication; AI findings grounded against real lines.
- Patch guard: patches that swallow exceptions or add `noqa`/`type: ignore`/`nosec` are rejected without a model call.
- Prompt-injection hardening: untrusted-data rule in all prompts, injection-pattern flagging and labelling, secret masking in context.
- Citation checks for `file:line` references (grounded / unretrieved / invalid) with a warning on invalid ones.
- Symlink safety in indexing and local copy.
- Tool failures reported as `TOOL FAILED`; any tool exception handled; `MAX_RUN_SECONDS` limit and cancel hook in the runtime.
- Verification fixes: regression "passed after" requires the tests to have run; regression tests that fail only on a missing symbol do not count as reproduction; tests not run are never "fixed".
- Test selection from changed files and the import graph with a fast targeted gate.
- Agent-outcome metrics (`python -m app.rag.eval agent`): root-cause accuracy, citation validity, patch success, regression effectiveness, with offline-mock vs real-provider labelling.

## Measured results
- Retrieval, offline hash embedder, 50 questions: best config MRR 0.339, Recall@5 0.420 (`eval/results/offline_baseline_codebase_agent.md`).
- Agent outcomes, offline mock, 4 cases on the `delivery_sync` fixture: expected file in context 4/4; all model-dependent metrics n/a (`eval/results/agent_offline_mock_delivery_sync.md`).
- No real-LLM, real-embedding or patch-success numbers exist yet.

## Remaining limitations
- Real-provider prompt quality unmeasured; run `python -m app.rag.eval agent ... --provider gemini` and a real-embedder sweep.
- Real Docker, real GitHub and browser flows unverified.
- Cancel hook is not wired to an API endpoint. The file-viewer endpoint does not refuse secret files (agent tools do).
- The exact source shown to the coder is not secret-masked (edits are matched literally).
- Static call-graph resolution is name-based; dynamic dispatch is only resolved when the name is unique.
- Single local user; no accounts, RBAC or hosted deployment.
- Injection pattern-flagging cannot catch every phrasing; approval and the sandbox are the backstops.

## History
v13 hardening and review/eval work (above) · v12 Docker sandbox, quality dashboard, git intelligence, GitHub workflows · v11 tool system, debugging agent, patch engine · v10 LLM layer and multi-specialist agent · v7 RAG pipeline and experiments · v6 repository management and code intelligence · v5 Next.js IDE · v4 architecture, review, change, tests, PRs · v3 web UI · v2 retrieval fixes · v1 backend core.
