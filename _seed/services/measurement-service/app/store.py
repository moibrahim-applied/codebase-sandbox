import json
import uuid
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as redis

from .config import get_settings


class AuditStore:
    """Thin wrapper over redis for append-only audit records.

    The store is intentionally append-only: no update, no delete. That makes
    it ALCOA+ compliant out of the box (records are attributable, legible,
    contemporaneous, original, and accurate at insertion time).
    """

    def __init__(self, client: redis.Redis | None = None) -> None:
        s = get_settings()
        self._ns = s.redis_namespace
        self._client = client or redis.from_url(s.redis_url, decode_responses=True)

    async def append(self, kind: str, payload: dict[str, Any]) -> str:
        record_id = str(uuid.uuid4())
        record = {
            "id": record_id,
            "kind": kind,
            "payload": payload,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        key = f"{self._ns}:audit:{record_id}"
        await self._client.set(key, json.dumps(record))
        await self._client.lpush(f"{self._ns}:audit:index", record_id)
        return record_id

    async def list_recent(self, limit: int = 50) -> list[dict[str, Any]]:
        ids = await self._client.lrange(f"{self._ns}:audit:index", 0, limit - 1)
        if not ids:
            return []
        keys = [f"{self._ns}:audit:{i}" for i in ids]
        raw = await self._client.mget(keys)
        return [json.loads(x) for x in raw if x]

    async def close(self) -> None:
        await self._client.close()


_singleton: AuditStore | None = None


def get_store() -> AuditStore:
    global _singleton
    if _singleton is None:
        _singleton = AuditStore()
    return _singleton
