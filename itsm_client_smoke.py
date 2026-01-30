#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
from fastmcp import Client



async def main() -> None:
    async with Client(SERVER_URL) as client:
        print("\n=== Tools ===")
        for t in await client.list_tools():
            print(f"- {t.name}")

        print("\n=== Call: incident_pack (structured output + resource URIs) ===")
        pack = json.loads(pack_resp.content[0].text)
        print(json.dumps(pack, indent=2))

        print("\n=== Fetch suggested resources from incident_pack ===")

        print("\n=== Create research plan (tool -> resource URI) ===")
        created = json.loads(created_resp.content[0].text)
        print(json.dumps(created, indent=2))

        print("\n=== Read research plan resource ===")
        plan = await client.read_resource(created["resource_uri"])
        print(plan[0].text)

        print("\n=== Get prompt: ask_clarifying_questions ===")
        for i, msg in enumerate(prompt.messages, start=1):
            print(f"\n--- Prompt message {i} ({msg.role}) ---")
            print(msg.content)


if __name__ == "__main__":
    asyncio.run(main())
