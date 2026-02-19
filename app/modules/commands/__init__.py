from app.modules.commands.registry import registry, CommandSpec
from app.modules.commands.schemas import (
    RunCmdPayload,
    RunScriptPayload,
    KillProcessPayload,
    BlockProcessPayload,
)

registry.register(CommandSpec("RUN_CMD", RunCmdPayload))
registry.register(CommandSpec("RUN_SCRIPT", RunScriptPayload))
registry.register(CommandSpec("KILL_PROCESS", KillProcessPayload))
registry.register(CommandSpec("BLOCK_PROCESS", BlockProcessPayload))
