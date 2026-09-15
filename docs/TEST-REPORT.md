# Test Report

**System:** AI Call Center MVP

**Test date:** 2026-09-15

**Environment:** Windows local Docker Compose; deterministic local provider adapters (no model weights downloaded)
**Scope:** Implemented API, web shell, realtime gateway, Compose topology and automated API tests.

## Result summary

| Area | Cases | Status | Evidence |
|---|---:|---|---|
| Authentication, RBAC and audit | TC-006, TC-017, TC-018 | PASS | `pytest -q`: authenticated audit/dashboard coverage passed |
| Session state validation | TC-006, TC-007 | PASS | `pytest -q`: valid startup and invalid completion transition coverage passed |
| Form correction/history/no unknown field | TC-009, TC-011 | PASS | `pytest -q`: correction, immutable history and unknown-field rejection passed |
| Upload validation | TC-003, TC-004 | PASS | `pytest -q`: empty and unsupported uploads rejected correctly |
| RAG collection isolation and provenance | TC-014, TC-015 | PASS | `pytest -q`: authorized result provenance and cross-collection denial passed |
| Docker build / service health | TC-020 | PASS with environment note | API/realtime health endpoints returned 200; web uses host port 3001 because port 3000 was already occupied |
| Browser microphone, real STT/LLM/TTS, OCR/PDF, n8n, Cloudflare | TC-001/2/5/8/12/13/16/19/21/22/23 | Not yet executable | Requires production adapters, browser/device and external configuration |

## Limitations / exit criteria

The repository must not report real Thai/English/Chinese speech quality, OCR accuracy, model latency, Cloudflare reachability, or n8n workflow delivery until real provider/model settings and test fixtures are supplied. The included deterministic adapters make API-contract and business-rule tests repeatable without exposing credentials or downloading unverified model weights.

## Executed commands

- `docker compose run --rm --no-deps api pytest -q` — **PASS: 6 passed in 0.80s**. One non-failing deprecation warning is emitted by Starlette's test client dependency.
- `docker compose build api` — **PASS**.
- `docker compose build realtime` — **PASS**.
- `docker compose build web` — **PASS**. The build completed, but npm reported dependency advisories; upgrade dependencies before production deployment.
- `docker compose up -d` plus `curl http://127.0.0.1:8000/health` and `curl http://127.0.0.1:8080/health` — **PASS**. API and realtime returned HTTP 200. Port 3000 was occupied by an existing local service, so this stack maps its web service to `127.0.0.1:3001`.

This report is updated after each test run with the exact command and result.
