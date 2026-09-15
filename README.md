# AI Call Center

Configuration-driven browser voice call center for multilingual intake, dynamic forms, grounded knowledge retrieval, and auditability.

## Quick start

1. Copy `.env.example` to `.env` and replace every placeholder secret (do not put real credentials in source control).
2. Run `docker compose up --build`.
3. Open `http://localhost:3001`; API documentation is at `http://localhost:8000/docs`.

PostgreSQL, Redis, MinIO, internal API and realtime services are private Docker-network services. Only the web/API/WebSocket loopback ports are mapped for local development. Add a reverse proxy and Cloudflare Tunnel only after HTTPS, authentication, and access policies are configured.

## Development and verification

API tests: `docker compose --env-file .env.example run --rm api pytest -q` (or use your local `.env`).

The default provider configuration uses deterministic adapters for a runnable test environment. Select real local STT/LLM/TTS/embedding adapters through Model Configuration after benchmarking hardware; UI code never calls models directly.

See [test cases](docs/TEST-CASES.md) and [test report](docs/TEST-REPORT.md).
