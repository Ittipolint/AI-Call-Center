"""Provider contracts and deterministic development adapters.

Production adapters belong behind these protocols; no route imports a model SDK.
"""
from dataclasses import dataclass
from typing import Protocol

@dataclass
class ProviderHealth:
    name: str
    version: str
    healthy: bool = True
    capabilities: tuple[str, ...] = ()

class STTProvider(Protocol):
    async def transcribe(self, audio: bytes, language: str | None = None) -> dict: ...
class LLMProvider(Protocol):
    async def generate(self, prompt: str) -> dict: ...
class TTSProvider(Protocol):
    async def synthesize(self, text: str, language: str, voice: str | None = None) -> bytes: ...
class EmbeddingProvider(Protocol):
    async def embed(self, texts: list[str]) -> list[list[float]]: ...
class OCRProvider(Protocol):
    async def extract(self, document: bytes) -> str: ...

class DeterministicSTT:
    async def transcribe(self, audio: bytes, language: str | None = None) -> dict:
        # Test adapter: audio files containing UTF-8 text are accepted as transcript fixtures.
        return {"text": audio.decode("utf-8", errors="replace"), "language": language or "th", "confidence": 1.0}

class DeterministicLLM:
    async def generate(self, prompt: str) -> dict:
        return {"text": "รับทราบข้อมูลแล้ว กรุณาให้รายละเอียดเพิ่มเติมเท่าที่สะดวกค่ะ", "structured": {}}

class DeterministicTTS:
    async def synthesize(self, text: str, language: str, voice: str | None = None) -> bytes:
        return text.encode("utf-8")
