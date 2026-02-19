import asyncio
import json
from app.redis.client import redis_client
from app.redis.keys import EVENT_STREAM, PUBSUB_PREFIX
from app.redis.state_repo import PcStateRepo
from app.redis.events import publish_to_pc_channel
from app.shared.pc_mapper import map_state_to_computer_dto


GROUP = "ws-fanout"
CONSUMER = "ws-fanout-1"

async def ensure_group():
    try:
        await redis_client.xgroup_create(EVENT_STREAM, GROUP, id="0-0", mkstream=True)
    except Exception:
        pass

async def stream_to_pubsub_fanout():
    """
    Надежная доставка: читаем stream (xreadgroup) и публикуем в pubsub по pc_id.
    PubSub доставит всем WS инстансам (если их много).
    """
    await ensure_group()
    while True:
        resp = await redis_client.xreadgroup(
            groupname=GROUP,
            consumername=CONSUMER,
            streams={EVENT_STREAM: ">"},
            count=50,
            block=5000,
        )
        if not resp:
            continue

        for _, messages in resp:
            for msg_id, fields in messages:
                data = json.loads(fields["data"])
                pc_id = data["pc_id"]
                await publish_to_pc_channel(pc_id, data)
                await redis_client.xack(EVENT_STREAM, GROUP, msg_id)

async def pubsub_to_ws_delivery(broker):
    """
    Каждый WS-инстанс подписан на сообщения pubsub.
    Если подписок много, можно оптимизировать: подписываться по pc_id динамически.
    Сейчас — простая версия: psubscribe на все pc:pubsub:*.
    """
    state_repo = PcStateRepo()
    pubsub = redis_client.pubsub()
    await pubsub.psubscribe(PUBSUB_PREFIX + "*")

    while True:
        msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
        if not msg:
            await asyncio.sleep(0.01)
            continue

        try:
            payload = json.loads(msg["data"])
            pc_id = payload["pc_id"]
            #changed = set(payload.get("changed", []))
        except Exception:
            continue

        if payload.get("type") in ("command_update", "task_update"):
            for ws in broker.targets_for_pc(pc_id):
                try:
                    await ws.send_json({"type": payload["type"], "data": payload})
                except Exception:
                    pass
            continue

        state = await state_repo.get_state(pc_id)
        dto = map_state_to_computer_dto(
            pc_id,
            meta=state.get("meta") or {},
            metrics=state.get("metrics") or {},
            procs=state.get("procs"),
        )

        for ws in broker.targets_for_pc(pc_id):
            try:
                await ws.send_json({"type": "pc_update", "data": dto})
            except Exception:
                pass

async def run_ws_fanout_consumers(broker):
    await asyncio.gather(
        stream_to_pubsub_fanout(),
        pubsub_to_ws_delivery(broker),
    )
