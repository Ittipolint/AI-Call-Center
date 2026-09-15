from __future__ import annotations
import base64, hashlib, hmac, json, os, re, time, uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

app = FastAPI(title="AI Call Center API", version="1.0.0", openapi_url="/api/v1/openapi.json", docs_url="/docs")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "http://localhost:3001"], allow_methods=["*"], allow_headers=["*"], allow_credentials=True)
security = HTTPBearer(auto_error=False)
SECRET = os.getenv("JWT_SECRET", "development-only-change-me")
MAX_UPLOAD = int(os.getenv("MAX_UPLOAD_BYTES", "26214400"))
USERS = {os.getenv("ADMIN_EMAIL", "admin@example.local"): {"password": os.getenv("ADMIN_PASSWORD", "change-me-before-use"), "role": "Admin"}}
DB: dict[str, Any] = {"sessions": {}, "transcripts": defaultdict(list), "values": defaultdict(dict), "history": defaultdict(list), "audit": [], "roles": {}, "forms": {}, "collections": {}, "documents": {}, "models": {}}

FIELD_KEYS = "case_type report_date report_time reporter_phone reporter_gender behavior_type drug_type subject_full_name subject_gender subject_alias subject_age subject_physical_description subject_occupation subject_workplace subject_distinctive_characteristics weapon_description weapon_location vehicle_description subject_phone facebook_line_id other_assets relatives living_with location_place housing_project village_community soi road subdistrict district province location_characteristics directions_to_location drug_source_person_or_place drug_price drug_storage_location drug_use_behavior drug_use_duration drug_amount_per_day psychiatric_symptoms impact_or_hardship callback_requested callback_name callback_phone callback_preferred_time other_details do_not_notify_local_authority request_narcotics_agency_direct_action request_treatment do_not_want_arrest_prosecution_for_use_only".split()
STATE: dict[str, set[str]] = {
 "CREATED": {"READY", "FAILED", "ABANDONED"}, "READY": {"GREETING", "PAUSED", "FAILED"},
 "GREETING": {"LISTENING", "PAUSED", "FAILED"}, "LISTENING": {"THINKING", "PAUSED", "DISCONNECTED", "FAILED", "ESCALATED"},
 "THINKING": {"SPEAKING", "COLLECTING", "FAILED"}, "SPEAKING": {"LISTENING", "COLLECTING", "CONFIRMING"},
 "COLLECTING": {"LISTENING", "CONFIRMING", "PAUSED"}, "CONFIRMING": {"COMPLETED", "COLLECTING", "ESCALATED"},
 "PAUSED": {"LISTENING", "ABANDONED"}, "DISCONNECTED": {"LISTENING", "ABANDONED"}, "ESCALATED": {"COMPLETED"},
 "COMPLETED": set(), "FAILED": set(), "ABANDONED": set()}

def now() -> str: return datetime.now(timezone.utc).isoformat()
def ident() -> str: return str(uuid.uuid4())
def token(payload: dict) -> str:
    body = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")
    sig = hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"
def decode(raw: str) -> dict:
    try:
        body, sig = raw.split("."); expected = hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected): raise ValueError()
        payload = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
        if payload["exp"] < time.time(): raise ValueError()
        return payload
    except Exception: raise HTTPException(401, "Invalid or expired access token")
def user(creds: HTTPAuthorizationCredentials | None = Depends(security)) -> dict:
    if not creds: raise HTTPException(401, "Authentication required")
    return decode(creds.credentials)
def require(*allowed: str):
    def check(me: dict = Depends(user)):
        if me["role"] not in allowed: raise HTTPException(403, "Insufficient permission")
        return me
    return check
def audit(action: str, actor: str, target: str, details: dict | None = None):
    DB["audit"].append({"id": ident(), "at": now(), "actor": actor, "action": action, "target": target, "details": details or {}})
def session_or_404(session_id: str) -> dict:
    item = DB["sessions"].get(session_id)
    if not item: raise HTTPException(404, "Session not found")
    return item
def own_session(session_id: str, me: dict) -> dict:
    item = session_or_404(session_id)
    if me["role"] not in ("Admin", "Supervisor") and item["owner"] != me["sub"]: raise HTTPException(403, "Session is not assigned to you")
    return item
def transition(item: dict, next_state: str, actor: str):
    if next_state not in STATE.get(item["state"], set()): raise HTTPException(409, f"Invalid transition {item['state']} → {next_state}")
    item["state"] = next_state; item["updated_at"] = now(); audit("session.transition", actor, item["id"], {"state": next_state})

class Login(BaseModel): email: str; password: str
class CreateSession(BaseModel): role_id: str | None = None; form_id: str | None = None
class ManualValue(BaseModel): value: Any; status: Literal["CONFIRMED", "CORRECTED", "REJECTED", "NOT_PROVIDED"] = "CORRECTED"; reason: str | None = None
class RoleInput(BaseModel): name: str; description: str = ""; allowed_languages: list[str] = ["th", "en", "zh"]; form_id: str | None = None; active: bool = True
class PromptInput(BaseModel): content: str
class FormInput(BaseModel): name: str; fields: list[dict] = []
class CollectionInput(BaseModel): name: str; description: str = ""
class ModelInput(BaseModel): capability: Literal["stt", "llm", "tts", "embedding", "ocr"]; provider: str; model_name: str; enabled: bool = True

@app.get("/health")
def health(): return {"status": "ok", "service": "api", "time": now()}
@app.get("/metrics")
def metrics(): return "call_center_sessions_total %d\ncall_center_audit_events_total %d\n" % (len(DB["sessions"]), len(DB["audit"]))
@app.post("/api/v1/auth/login")
def login(body: Login):
    record = USERS.get(body.email)
    if not record or not hmac.compare_digest(record["password"], body.password): raise HTTPException(401, "Invalid credentials")
    payload = {"sub": body.email, "role": record["role"], "exp": time.time() + 900}
    audit("auth.login", body.email, body.email); return {"access_token": token(payload), "token_type": "bearer", "expires_in": 900}
@app.post("/api/v1/auth/refresh")
def refresh(me: dict = Depends(user)): return {"access_token": token({**{k:v for k,v in me.items() if k != 'exp'}, "exp": time.time()+900})}
@app.post("/api/v1/auth/logout")
def logout(me: dict = Depends(user)): audit("auth.logout", me["sub"], me["sub"]); return {"ok": True}
@app.get("/api/v1/auth/me")
def me(me: dict = Depends(user)): return {"email": me["sub"], "role": me["role"]}

@app.post("/api/v1/sessions")
def create_session(body: CreateSession, me: dict = Depends(require("Admin", "Supervisor", "Agent"))):
    sid = ident(); value = {"id": sid, "owner": me["sub"], "state": "CREATED", "role_id": body.role_id, "form_id": body.form_id or "drug-complaint-v1", "created_at": now(), "updated_at": now(), "snapshot": {"role_id": body.role_id, "form_id": body.form_id or "drug-complaint-v1"}}
    DB["sessions"][sid] = value; audit("session.create", me["sub"], sid); return value
@app.get("/api/v1/sessions")
def list_sessions(me: dict = Depends(user)):
    values = DB["sessions"].values(); return [v for v in values if me["role"] in ("Admin", "Supervisor") or v["owner"] == me["sub"]]
@app.get("/api/v1/sessions/{session_id}")
def get_session(session_id: str, me: dict = Depends(user)): return own_session(session_id, me)
def state_endpoint(target: str):
    def endpoint(session_id: str, me: dict = Depends(require("Admin", "Supervisor", "Agent"))):
        item = own_session(session_id, me); transition(item, target, me["sub"]); return item
    return endpoint
@app.post("/api/v1/sessions/{session_id}/start")
def start_session(session_id: str, me: dict = Depends(require("Admin", "Supervisor", "Agent"))):
    item = own_session(session_id, me)
    # Starting a browser call establishes the prepared state then enters listening.
    transition(item, "READY", me["sub"])
    transition(item, "GREETING", me["sub"])
    transition(item, "LISTENING", me["sub"])
    return item
app.post("/api/v1/sessions/{session_id}/pause")(state_endpoint("PAUSED"))
app.post("/api/v1/sessions/{session_id}/resume")(state_endpoint("LISTENING"))
app.post("/api/v1/sessions/{session_id}/complete")(state_endpoint("COMPLETED"))
app.post("/api/v1/sessions/{session_id}/escalate")(state_endpoint("ESCALATED"))

@app.get("/api/v1/sessions/{session_id}/transcript")
def transcript(session_id: str, me: dict = Depends(user)): own_session(session_id, me); return DB["transcripts"][session_id]
@app.post("/api/v1/sessions/{session_id}/transcript")
def add_transcript(session_id: str, body: dict, me: dict = Depends(require("Admin", "Supervisor", "Agent"))):
    own_session(session_id, me); items = DB["transcripts"][session_id]; item = {"segment_id": ident(), "session_id": session_id, "speaker": body.get("speaker", "caller"), "sequence_no": len(items)+1, "text": body.get("text", ""), "language": body.get("language", "th"), "is_final": bool(body.get("is_final", True)), "confidence": body.get("confidence"), "created_at": now()}; items.append(item); audit("transcript.create", me["sub"], item["segment_id"]); return item
@app.get("/api/v1/sessions/{session_id}/form")
def form(session_id: str, me: dict = Depends(user)): own_session(session_id, me); return {"session_id": session_id, "fields": DB["values"][session_id]}
@app.patch("/api/v1/sessions/{session_id}/form/fields/{field_key}")
def correct(session_id: str, field_key: str, body: ManualValue, me: dict = Depends(require("Admin", "Supervisor", "Agent"))):
    if field_key not in FIELD_KEYS: raise HTTPException(422, "Unknown form field")
    own_session(session_id, me); old = DB["values"][session_id].get(field_key)
    value = {"value": body.value, "status": body.status, "confidence": 1.0, "source_type": "human", "source_segment_ids": [], "updated_at": now(), "updated_by": me["sub"]}
    DB["values"][session_id][field_key] = value; DB["history"][session_id].append({"field_key": field_key, "before": old, "after": value, "reason": body.reason, "at": now()}); audit("form.correct", me["sub"], session_id, {"field": field_key}); return value
@app.get("/api/v1/sessions/{session_id}/form/history")
def form_history(session_id: str, me: dict = Depends(user)): own_session(session_id, me); return DB["history"][session_id]
@app.post("/api/v1/sessions/{session_id}/form/confirm")
def confirm_form(session_id: str, me: dict = Depends(require("Admin", "Supervisor", "Agent"))):
    own_session(session_id, me)
    for value in DB["values"][session_id].values():
        if value["status"] == "PROPOSED": value["status"] = "CONFIRMED"
    item = session_or_404(session_id)
    if item["state"] == "COLLECTING": transition(item, "CONFIRMING", me["sub"])
    audit("form.confirm", me["sub"], session_id); return {"ok": True, "state": item["state"]}

@app.post("/api/v1/audio/upload")
async def upload_audio(file: UploadFile = File(...), me: dict = Depends(require("Admin", "Supervisor", "Agent"))):
    content = await file.read()
    if not content: raise HTTPException(422, "Empty file")
    if len(content) > MAX_UPLOAD: raise HTTPException(413, "Upload exceeds configured limit")
    if file.content_type and not (file.content_type.startswith("audio/") or file.content_type == "text/plain"): raise HTTPException(415, "Unsupported audio content type")
    aid = ident(); audit("audio.upload", me["sub"], aid, {"bytes": len(content)}); return {"id": aid, "status": "queued", "bytes": len(content)}
@app.get("/api/v1/audio/{audio_id}")
def audio(audio_id: str, me: dict = Depends(user)): return {"id": audio_id, "status": "queued"}

def crud(kind: str):
    @app.get(f"/api/v1/{kind}")
    def list_items(me: dict = Depends(user)): return list(DB[kind].values())
    @app.post(f"/api/v1/{kind}")
    def create_item(body: dict, me: dict = Depends(require("Admin"))):
        item = {"id": ident(), **body, "created_at": now(), "updated_at": now()}; DB[kind][item["id"]] = item; audit(f"{kind}.create", me["sub"], item["id"]); return item
crud("roles"); crud("forms"); crud("collections"); crud("models")
@app.get("/api/v1/knowledge/collections")
def collections(me: dict = Depends(user)): return list(DB["collections"].values())
@app.post("/api/v1/knowledge/collections")
def create_collection(body: CollectionInput, me: dict = Depends(require("Admin"))):
    item = {"id": ident(), **body.model_dump(), "created_at": now()}; DB["collections"][item["id"]] = item; audit("collection.create", me["sub"], item["id"]); return item
@app.get("/api/v1/knowledge/documents")
def documents(me: dict = Depends(user)): return list(DB["documents"].values())
@app.post("/api/v1/knowledge/documents")
def create_document(body: dict, me: dict = Depends(require("Admin"))):
    if not body.get("collection_id") or not body.get("text"): raise HTTPException(422, "collection_id and text are required")
    item={"id": ident(), "status":"indexed", **body, "created_at":now()}; DB["documents"][item["id"]]=item; audit("knowledge.ingest", me["sub"],item["id"]); return item
@app.post("/api/v1/rag/retrieve")
def retrieve(body: dict, me: dict = Depends(user)):
    q=body.get("query", "").lower(); allowed=set(body.get("allowed_collection_ids", [])); results=[]
    for doc in DB["documents"].values():
        if allowed and doc.get("collection_id") not in allowed: continue
        text=doc.get("text", ""); score=sum(1 for word in q.split() if word in text.lower()) / max(len(q.split()), 1)
        if score >= float(body.get("similarity_threshold", .01)): results.append({"document_id":doc["id"],"collection_id":doc["collection_id"],"text":text[:1000],"score":score,"provenance":{"source_filename":doc.get("filename","inline")}})
    return {"request_id":body.get("request_id",ident()),"results":sorted(results,key=lambda r:r["score"],reverse=True)[:body.get("top_k",8)]}
@app.get("/api/v1/dashboard/summary")
def dashboard(me: dict = Depends(user)): return {"sessions_total":len(DB["sessions"]), "by_state":{s:sum(1 for x in DB["sessions"].values() if x["state"]==s) for s in STATE}, "audit_events":len(DB["audit"])}
@app.get("/api/v1/dashboard/realtime")
def dashboard_realtime(me: dict = Depends(user)): return {"active_sessions":sum(1 for x in DB["sessions"].values() if x["state"] in {"LISTENING","THINKING","SPEAKING","COLLECTING"})}
@app.get("/api/v1/reports/{report_name}")
def report(report_name: str, me: dict = Depends(require("Admin", "Supervisor"))): return {"report":report_name,"generated_at":now(),"rows":list(DB["sessions"].values())}
@app.get("/api/v1/audit/events")
def audit_events(me: dict = Depends(require("Admin", "Supervisor"))): return DB["audit"]

# Seed configuration makes the form a data concern rather than a UI concern.
DB["forms"]["drug-complaint-v1"] = {"id":"drug-complaint-v1", "name":"Drug Complaint", "version":1, "published":True, "fields":[{"key":k,"label":k.replace("_"," "),"enabled":True} for k in FIELD_KEYS]}
