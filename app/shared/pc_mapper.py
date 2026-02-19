import time

def _human_last_seen(last_seen_ts: int) -> str:
    if not last_seen_ts:
        return "никогда"
    seconds = max(0, int(time.time()) - int(last_seen_ts))
    if seconds < 60:
        return "0 мин назад"
    return f"{seconds // 60} мин назад"


def map_state_to_computer_dto(pc_id: str, *, meta: dict, metrics: dict, procs: dict | None) -> dict:
    last_seen = int(meta.get("last_seen", 0) or 0)
    online = meta.get("online") in ("1", 1, True, "true")

    items = []
    if isinstance(procs, dict):
        items = procs.get("items") or []
    process_count = len(items) if isinstance(items, list) else 0

    process_list = []
    if isinstance(procs, dict):
        items = procs.get("items") or []
        if isinstance(items, list):
            for p in items[:1000]:
                process_list.append({
                    "pid": p.get("pid"),
                    "name": p.get("name"),
                    "cpu": p.get("cpu", 0),
                    "memoryMb": p.get("memory", p.get("memoryMb", 0)),
                    "status": p.get("status", "running"),
                    "blocked": bool(p.get("blocked", False)),
                })

    return {
        "id": pc_id,
        "computerActive": bool(online),
        "computerName": meta.get("hostname") or "Unknown",
        "computerMacAddress": meta.get("mac") or "—",
        "lastTimeActive": _human_last_seen(last_seen),
        "processes": f"{process_count} процессов",
        "processList": process_list,

        "cpu": {"value": int(metrics.get("cpu", 0) or 0)},
        "ozu": {"value": int(metrics.get("ram", 0) or 0)},
        "hard_drive": {"value": int(metrics.get("disk", 0) or 0)},

        "system": {
            "osName": meta.get("os_name"),
            "osVersion": meta.get("os_version"),
            "osBuild": (str(meta.get("os_build")) if meta.get("os_build") is not None else None),
            "ip": meta.get("ip"),
            "username": meta.get("username"),
        },
    }
