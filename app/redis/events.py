import json
from app.redis.client import redis_client
from app.redis.keys import EVENT_STREAM, PUBSUB_PREFIX

async def emit_state_changed(pc_id: str, changed: list[str], ver: int) -> None:
    payload = {"pc_id": pc_id, "changed": changed, "ver": ver}
    await redis_client.xadd(EVENT_STREAM, {"data": json.dumps(payload)}, maxlen=10000, approximate=True)

async def publish_to_pc_channel(pc_id: str, message: dict) -> None:
    await redis_client.publish(PUBSUB_PREFIX + pc_id, json.dumps(message))
