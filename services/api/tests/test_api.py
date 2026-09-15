from fastapi.testclient import TestClient
from app.main import DB, FIELD_KEYS, app

client = TestClient(app)

def auth():
    response = client.post("/api/v1/auth/login", json={"email":"admin@example.local","password":"change-me-before-use"})
    assert response.status_code == 200
    return {"Authorization": "Bearer " + response.json()["access_token"]}

def clean():
    for key in ("sessions", "transcripts", "values", "history", "audit", "roles", "collections", "documents", "models"):
        DB[key].clear()

def test_login_rejects_invalid_password():
    clean()
    assert client.post("/api/v1/auth/login", json={"email":"admin@example.local","password":"wrong"}).status_code == 401

def test_session_state_machine_and_authorized_access():
    clean(); headers = auth()
    created = client.post("/api/v1/sessions", json={}, headers=headers).json()
    assert created["state"] == "CREATED"
    started = client.post(f"/api/v1/sessions/{created['id']}/start", headers=headers).json()
    assert started["state"] == "LISTENING"
    assert client.post(f"/api/v1/sessions/{created['id']}/complete", headers=headers).status_code == 409
    assert client.post(f"/api/v1/sessions/{created['id']}/pause", headers=headers).status_code == 200
    assert client.post(f"/api/v1/sessions/{created['id']}/resume", headers=headers).json()["state"] == "LISTENING"

def test_human_correction_keeps_history_and_rejects_unknown_field():
    clean(); headers = auth(); sid = client.post("/api/v1/sessions", json={}, headers=headers).json()["id"]
    assert client.patch(f"/api/v1/sessions/{sid}/form/fields/not_a_real_field", json={"value":"x"}, headers=headers).status_code == 422
    fixed = client.patch(f"/api/v1/sessions/{sid}/form/fields/subject_age", json={"value":35,"status":"CORRECTED","reason":"caller corrected age"}, headers=headers)
    assert fixed.status_code == 200 and fixed.json()["source_type"] == "human"
    history = client.get(f"/api/v1/sessions/{sid}/form/history", headers=headers).json()
    assert history[0]["after"]["value"] == 35

def test_upload_defends_empty_and_bad_content_type():
    clean(); headers = auth()
    assert client.post("/api/v1/audio/upload", files={"file":("empty.wav",b"","audio/wav")}, headers=headers).status_code == 422
    assert client.post("/api/v1/audio/upload", files={"file":("danger.exe",b"x","application/octet-stream")}, headers=headers).status_code == 415

def test_rag_collection_authorization_and_provenance():
    clean(); headers = auth()
    collection = client.post("/api/v1/knowledge/collections", json={"name":"policy"}, headers=headers).json()
    document = client.post("/api/v1/knowledge/documents", json={"collection_id":collection["id"],"text":"The callback service is available Monday through Friday.","filename":"policy.txt"}, headers=headers).json()
    found = client.post("/api/v1/rag/retrieve", json={"query":"callback service","allowed_collection_ids":[collection["id"]],"similarity_threshold":0.01}, headers=headers).json()
    assert found["results"][0]["document_id"] == document["id"]
    denied = client.post("/api/v1/rag/retrieve", json={"query":"callback service","allowed_collection_ids":["another-collection"],"similarity_threshold":0.01}, headers=headers).json()
    assert denied["results"] == []

def test_dashboard_and_audit_are_available_to_admin():
    clean(); headers = auth(); client.post("/api/v1/sessions",json={},headers=headers)
    assert client.get("/api/v1/dashboard/summary",headers=headers).json()["sessions_total"] == 1
    assert len(client.get("/api/v1/audit/events",headers=headers).json()) >= 1
