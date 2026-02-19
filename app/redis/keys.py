def pc_meta(pc_id: str) -> str:
    return f"pc:{pc_id}:meta"

def pc_metrics(pc_id: str) -> str:
    return f"pc:{pc_id}:metrics"

def pc_procs(pc_id: str) -> str:
    return f"pc:{pc_id}:procs"

def pc_ver(pc_id: str) -> str:
    return f"pc:{pc_id}:ver"

ONLINE_ZSET = "pc:index:online"

# streams + pubsub
EVENT_STREAM = "pc:events"
PUBSUB_PREFIX = "pc:pubsub:"  # + pc_id
