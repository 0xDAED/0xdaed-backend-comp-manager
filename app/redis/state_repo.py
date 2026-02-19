import json
import time
from typing import Any

from app.redis.client import redis_client

PC_EVENTS_STREAM = "pc:events"

DEFAULT_TTL_SECONDS = 60  # можешь вынести в settings


class PcStateRepo:
    def __init__(self, ttl_seconds: int = DEFAULT_TTL_SECONDS):
        self.ttl = ttl_seconds

    # ---------- helpers ----------
    def _k_meta(self, pc_id: str) -> str:
        return f"pc:{pc_id}:meta"

    def _k_metrics(self, pc_id: str) -> str:
        return f"pc:{pc_id}:metrics"

    def _k_procs(self, pc_id: str) -> str:
        return f"pc:{pc_id}:procs"

    def _k_ver(self, pc_id: str) -> str:
        return f"pc:{pc_id}:ver"

    def _k_known(self) -> str:
        return "pc:index:known"

    def _k_online(self) -> str:
        return "pc:index:online"

    async def _publish_event(self, pc_id: str, changed: list[str], ver: int) -> None:
        payload = {"pc_id": pc_id, "changed": changed, "ver": ver, "ts": time.time()}
        await redis_client.xadd(PC_EVENTS_STREAM, {"data": json.dumps(payload)})

    async def _bump_ver(self, pc_id: str) -> int:
        ver = await redis_client.incr(self._k_ver(pc_id))
        await redis_client.expire(self._k_ver(pc_id), self.ttl)
        return int(ver)

    # ---------- public API ----------
    async def touch_online(self, pc_id: str, seq: int | None = None) -> int:
        """
        Отмечает ПК как online, обновляет last_seen и TTL.
        """
        now = int(time.time())
        k = self._k_meta(pc_id)

        pipe = redis_client.pipeline()
        pipe.hset(k, mapping={"online": "1", "last_seen": str(now)})
        if seq is not None:
            pipe.hset(k, "last_seq", str(seq))
        pipe.expire(k, self.ttl)

        # индексы
        pipe.sadd(self._k_known(), pc_id)
        pipe.zadd(self._k_online(), {pc_id: float(now)})

        await pipe.execute()

        ver = await self._bump_ver(pc_id)
        await self._publish_event(pc_id, ["meta"], ver)
        return ver

    async def upsert_meta(self, pc_id: str, meta: dict[str, Any], seq: int | None = None) -> int:
        """
        Обновляет meta-данные (hostname, os, ip, user, mac...)
        """
        now = int(time.time())
        k = self._k_meta(pc_id)

        # приводим значения к строкам для стабильности хранения
        mapping: dict[str, str] = {}
        for key, val in meta.items():
            if val is None:
                continue
            if key == "os_build":
                mapping[key] = str(val)  # важный фикс
            else:
                mapping[key] = str(val)

        mapping["online"] = "1"
        mapping["last_seen"] = str(now)
        if seq is not None:
            mapping["last_seq"] = str(seq)

        pipe = redis_client.pipeline()
        pipe.hset(k, mapping=mapping)
        pipe.expire(k, self.ttl)
        pipe.sadd(self._k_known(), pc_id)
        pipe.zadd(self._k_online(), {pc_id: float(now)})

        await pipe.execute()

        ver = await self._bump_ver(pc_id)
        await self._publish_event(pc_id, ["meta"], ver)
        return ver

    async def upsert_metrics(self, pc_id: str, metrics: dict[str, Any], seq: int | None = None) -> int:
        """
        Обновляет метрики (cpu/ram/disk). TTL держим через meta.touch_online().
        Но на всякий случай продлеваем и здесь.
        """
        now = int(time.time())
        k_m = self._k_metrics(pc_id)
        k_meta = self._k_meta(pc_id)

        mapping = {}
        for key, val in metrics.items():
            if val is None:
                continue
            mapping[key] = str(int(val)) if isinstance(val, (int, float)) else str(val)

        pipe = redis_client.pipeline()
        if mapping:
            pipe.hset(k_m, mapping=mapping)
            pipe.expire(k_m, self.ttl)

        # touch online, чтобы ПК не “отваливался” если он шлёт только метрики
        pipe.hset(k_meta, mapping={"online": "1", "last_seen": str(now)})
        if seq is not None:
            pipe.hset(k_meta, "last_seq", str(seq))
        pipe.expire(k_meta, self.ttl)

        pipe.sadd(self._k_known(), pc_id)
        pipe.zadd(self._k_online(), {pc_id: float(now)})

        await pipe.execute()

        ver = await self._bump_ver(pc_id)
        await self._publish_event(pc_id, ["metrics", "meta"], ver)
        return ver

    async def upsert_processes(self, pc_id: str, items: list[dict[str, Any]], seq: int | None = None) -> int:
        """
        Обновляет процессы. Храним как JSON в строке.
        """
        now = int(time.time())
        k_p = self._k_procs(pc_id)
        k_meta = self._k_meta(pc_id)

        data = json.dumps({"items": items}, ensure_ascii=False)

        pipe = redis_client.pipeline()
        pipe.set(k_p, data, ex=self.ttl)

        # touch online
        pipe.hset(k_meta, mapping={"online": "1", "last_seen": str(now)})
        if seq is not None:
            pipe.hset(k_meta, "last_seq", str(seq))
        pipe.expire(k_meta, self.ttl)

        pipe.sadd(self._k_known(), pc_id)
        pipe.zadd(self._k_online(), {pc_id: float(now)})

        await pipe.execute()

        ver = await self._bump_ver(pc_id)
        await self._publish_event(pc_id, ["procs", "meta"], ver)
        return ver

    async def get_state(self, pc_id: str) -> dict[str, Any]:
        k_meta = self._k_meta(pc_id)
        k_m = self._k_metrics(pc_id)
        k_p = self._k_procs(pc_id)

        pipe = redis_client.pipeline()
        pipe.hgetall(k_meta)
        pipe.hgetall(k_m)
        pipe.get(k_p)
        meta_raw, metrics_raw, procs_raw = await pipe.execute()

        meta = dict(meta_raw or {})
        metrics = dict(metrics_raw or {})

        procs = None
        if procs_raw:
            try:
                procs = json.loads(procs_raw)
            except Exception:
                procs = None

        return {"meta": meta, "metrics": metrics, "procs": procs}
