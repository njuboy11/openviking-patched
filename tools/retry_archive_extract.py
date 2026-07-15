#!/usr/bin/env python3
"""
Retry a failed archive's Phase 2 (memory extraction).

Usage:
    python3 retry_archive_extract.py <session_id> <archive_index>

Example:
    python3 retry_archive_extract.py dc2ffc00-245a-498b-afef-b4fe51da902f 17

Prerequisites:
    OV server must be installed and config loaded (ov.conf).
    Script runs inside the OV Python environment.
"""
import asyncio, json, sys, os

OV_DIST = "/usr/local/lib/python3.12/dist-packages"
if OV_DIST not in sys.path:
    sys.path.insert(0, OV_DIST)

from openviking.service.session_service import get_service
from openviking.service.task_tracker import get_task_tracker
from openviking.context import RequestContext, User, Role
from openviking.message import Message

async def retry_extract(session_id: str, archive_index: int):
    ctx = RequestContext(
        user=User(user_id="main"),
        role=Role.ROOT,
        account_id="default",
    )

    service = get_service()
    session = await service.sessions.get(session_id, ctx)
    viking_fs = session._viking_fs
    archive_uri = f"{session._session_uri}/history/archive_{archive_index:03d}"

    # 1 ── check .failed.json exists ──
    try:
        failed_data = await viking_fs.read_file(f"{archive_uri}/.failed.json", ctx=ctx)
        failed_info = json.loads(failed_data)
        print(f"✓ .failed.json found: failed_at={failed_info.get('failed_at','?')} "
              f"reason={failed_info.get('reason','?')[:80]}")
    except Exception:
        print(f"✗ archive_{archive_index:03d} has no .failed.json — nothing to retry")
        return

    # 2 ── read archived messages ──
    try:
        content = await viking_fs.read_file(f"{archive_uri}/messages.jsonl", ctx=ctx)
    except Exception as e:
        print(f"✗ Cannot read messages.jsonl: {e}")
        return

    messages = []
    for line in content.strip().split("\n"):
        if not line.strip():
            continue
        try:
            messages.append(Message.from_dict(json.loads(line)))
        except Exception:
            continue

    if not messages:
        print(f"✗ archive_{archive_index:03d} has no messages")
        return
    print(f"✓ Read {len(messages)} messages")

    # 3 ── delete .failed.json (reset state) ──
    try:
        await viking_fs.delete_file(f"{archive_uri}/.failed.json", ctx=ctx)
        print(f"✓ Deleted .failed.json")
    except Exception as e:
        print(f"✗ Cannot delete .failed.json: {e}")
        return

    # 4 ── create task + run Phase 2 in background ──
    usage_records = []
    first_id = messages[0].id if messages else ""
    last_id = messages[-1].id if messages else ""

    tracker = get_task_tracker()
    task = await tracker.create(
        "archive_retry",
        resource_id=f"{session_id}:archive_{archive_index:03d}",
        account_id="default",
        user_id="main",
    )
    await tracker.start(task.task_id, account_id="default", user_id="main")

    # Fire Phase 2 (runs asyncio.create_task inside _run_memory_extraction)
    extract_task = asyncio.create_task(
        session._run_memory_extraction(
            task_id=task.task_id,
            archive_uri=archive_uri,
            messages=messages,
            usage_records=usage_records,
            first_message_id=first_id,
            last_message_id=last_id,
            memory_policy=None,
        )
    )

    print(f"\n✅ Retry started for archive_{archive_index:03d}")
    print(f"   task_id: {task.task_id}")
    print(f"   archive: {archive_uri}")
    print(f"   messages: {len(messages)}")
    print(f"\n   Track: GET /api/v1/sessions/{session_id}/commits/{task.task_id}")

    try:
        await extract_task
        print(f"\n✅ archive_{archive_index:03d} Phase 2 completed")
    except Exception as e:
        print(f"\n❌ archive_{archive_index:03d} Phase 2 failed: {e}")

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 retry_archive_extract.py <session_id> <archive_index>")
        print("Example: python3 retry_archive_extract.py dc2ffc00-... 17")
        sys.exit(1)
    asyncio.run(retry_extract(sys.argv[1], int(sys.argv[2])))

if __name__ == "__main__":
    main()
