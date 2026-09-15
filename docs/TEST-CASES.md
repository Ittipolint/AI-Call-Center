# Test Cases

This suite is traceable to RS FR/NFR/AC and TS §36–37. Automated cases run in `services/api/tests`; the manual/E2E cases are executable against the Docker deployment.

| ID | Requirement | Preconditions | Steps | Expected result | Type |
|---|---|---|---|---|---|
| TC-001 | FR-001, AC-01 | Signed-in agent, active session | Allow microphone; start/stop recording | Gateway accepts ordered audio events and emits state/transcript events | E2E |
| TC-002 | FR-001 | Active session | Deny browser microphone permission | UI gives actionable message; session is not corrupted | E2E |
| TC-003 | FR-002 | Signed-in agent | Upload an audio MIME type within configured limit | Asset is accepted and queued | Integration |
| TC-004 | FR-002, NFR security | Signed-in agent | Upload empty file and executable MIME | Empty file is rejected with 422; unsupported type with 415 | Automated |
| TC-005 | FR-003, AC-02 | Provider configured | Submit Thai, English and Chinese fixtures | Language and final transcript are retained per segment | Integration |
| TC-006 | FR-004, AC-03 | New session | Create then start a session | Persisted state progresses CREATED→READY→GREETING→LISTENING | Automated |
| TC-007 | FR-004 | Listening session | Complete the session directly | Invalid transition is rejected with 409 | Automated |
| TC-008 | FR-005, FR-010, AC-04 | Active dynamic form | Submit one final segment containing multiple facts | All supported fields are proposed with evidence | AI evaluation |
| TC-009 | FR-005, FR-012, AC-05 | Active dynamic form | Submit ambiguous/no-evidence assertion | No factual value is confirmed; value is proposed/conflicted/unknown | AI evaluation |
| TC-010 | FR-009, AC-08 | Admin | Read Drug Complaint form seed | Form data contains all specified field keys; UI does not hard-code them | Automated/manual |
| TC-011 | FR-011, AC-18 | Signed-in agent | Correct `subject_age`; inspect form history/audit | Human value is marked CORRECTED, prior history is retained, audit created | Automated |
| TC-012 | FR-006/007, AC-11 | Admin | Create role, prompt draft, publish new version | Published version is immutable and session snapshot retains version | Integration |
| TC-013 | FR-014, AC-09 | Admin collection | Ingest text/PDF/image and wait for worker | Chunks carry document/collection/page/source/version/language metadata | Integration |
| TC-014 | FR-015, AC-10/20 | Authorized collection | Retrieve matching and nonmatching query | Match has provenance; no result returns uncertainty rather than invented answer | Automated |
| TC-015 | FR-017, AC-15 | Two roles/collections/sessions | Query a collection not assigned to session | Result set is empty; no cross-session/collection data appears | Automated |
| TC-016 | FR-018 | TTS adapter enabled | Synthesize Thai, English, Chinese response | Audio is returned through adapter and failure is surfaced safely | Integration |
| TC-017 | FR-019/020, AC-13/14 | Sessions exist | View dashboard and request report with filter | Counts and rows are scoped by authorization | Automated/manual |
| TC-018 | FR-021/022 | Supervisor | Search session and audit events | Transcript/form provenance and actor/timestamp are visible | Integration |
| TC-019 | FR-023/024, AC-19/21/22 | n8n profile off/on | Trigger post-call event, repeat same event ID, then stop n8n | Core flow works when off; duplicates are idempotent; failure is isolated/logged | Integration |
| TC-020 | NFR-001, AC-16 | Clean Docker host | `docker compose up --build` | All required health checks pass; only intended loopback ports are mapped | Deployment |
| TC-021 | NFR-004, AC-17 | Cloudflare configured | Access public hostname and verify service ports | HTTPS web/API/WS route works; DB/Redis/MinIO/model services remain private | Manual security |
| TC-022 | NFR-006/007 | Running deployment | Stop provider/RAG and inspect health/logs/metrics | User-safe error, correlation-ready JSON log, metric and recovery behavior | Integration |
| TC-023 | AC-15 | Two agent accounts | Interleave sessions and transcript/form updates | Data and state remain isolated | E2E |

## AI evaluation fixtures

Before accepting a real model, add Thai/English/Chinese audio-plus-reference fixtures for clear facts, ambiguity, corrections, negations, multi-fact turns, hallucination traps and RAG questions with/without evidence. Record WER, field extraction accuracy, unsupported-fact rate, grounded-answer rate, provenance completeness and latency. Real-model benchmarking is intentionally not claimed by the deterministic development adapter.
