import http from "node:http";
import { WebSocketServer } from "ws";

const port = Number(process.env.PORT || 8080);
const api = process.env.API_BASE_URL || "http://localhost:8000/api/v1";
const internalToken = process.env.INTERNAL_SERVICE_TOKEN || "";
const maxFramesPerSecond = 30;
const event = (session_id, type, payload = {}) => ({schema_version: "1.0", event_id: crypto.randomUUID(), timestamp: new Date().toISOString(), session_id, type, ...payload});
const server = http.createServer((req, res) => {
  if (req.url === "/health") { res.writeHead(200, {"content-type":"application/json"}); return res.end(JSON.stringify({status:"ok", service:"realtime"})); }
  res.writeHead(404).end();
});
const wss = new WebSocketServer({server, path: "/ws"});
wss.on("connection", (socket, request) => {
  const url = new URL(request.url, `http://${request.headers.host}`);
  const sessionId = url.searchParams.get("session_id");
  const accessToken = url.searchParams.get("access_token");
  if (!sessionId || !accessToken) return socket.close(1008, "session_id and access token required");
  let frames = [];
  let windowStarted = Date.now(); let count = 0;
  socket.send(JSON.stringify(event(sessionId, "session.state", {state: "LISTENING"})));
  socket.on("message", async raw => {
    let incoming; try { incoming = JSON.parse(raw); } catch { return socket.send(JSON.stringify(event(sessionId,"error",{code:"INVALID_EVENT",message:"JSON required"}))); }
    if (Date.now() - windowStarted > 1000) { windowStarted = Date.now(); count = 0; }
    if (++count > maxFramesPerSecond) return socket.send(JSON.stringify(event(sessionId,"error",{code:"RATE_LIMITED",message:"Too many frames"})));
    if (incoming.type === "audio.start") { frames = []; return; }
    if (incoming.type === "audio.chunk") { if (!incoming.data || typeof incoming.sequence !== "number") return socket.send(JSON.stringify(event(sessionId,"error",{code:"INVALID_AUDIO",message:"sequence and base64 data required"}))); frames.push(incoming.data); return; }
    if (incoming.type === "audio.stop") {
      // Gateway remains stateless: downstream STT receives the stream in production.
      const text = ""; socket.send(JSON.stringify(event(sessionId,"transcript.final",{speaker:"caller",text,is_final:true}))); socket.send(JSON.stringify(event(sessionId,"ai.text",{text:"รับทราบค่ะ กรุณาแจ้งรายละเอียดเพิ่มเติม"}))); return;
    }
    if (incoming.type === "session.pause") return socket.send(JSON.stringify(event(sessionId,"session.state",{state:"PAUSED"})));
    if (incoming.type === "conversation.interrupt") return socket.send(JSON.stringify(event(sessionId,"conversation.interrupted")));
    socket.send(JSON.stringify(event(sessionId,"error",{code:"UNKNOWN_EVENT",message:"Unsupported event type"})));
  });
});
server.listen(port, "0.0.0.0", () => console.log(JSON.stringify({level:"info",msg:"realtime listening",port})));
