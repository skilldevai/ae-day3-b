#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
from fastmcp import Client

SERVER_URL = "http://localhost:8000/mcp"


async def main() -> None:
    async with Client(SERVER_URL) as client:
        print("\n=== Tools ===")
        for t in await client.list_tools():
            print(f"- {t.name}")

        print("\n=== Call: incident_pack (structured output + resource URIs) ===")
        pack_resp = await client.call_tool(
            "incident_pack",
            {
                "short_description": "Users cannot login to internal app (SSO error).",
                "details": "Several users report 'invalid SAML response'. Started ~20 minutes ago.",
                "impact": "high",
                "urgency": "high",
                "customer_impacting": False,
                "max_kb_results": 3,
            },
        )
        pack = json.loads(pack_resp.content[0].text)
        print(json.dumps(pack, indent=2))

        print("\n=== Fetch suggested resources from incident_pack ===")
        for uri in pack["resources"]["policy_uris"] + pack["resources"]["kb_uris"]:
            res = await client.read_resource(uri)
            print(f"\n--- {uri} ---")
            print(res[0].text)

        print("\n=== Create research plan (tool -> resource URI) ===")
        created_resp = await client.call_tool(
            "create_research_plan",
            {
                "short_description": "Users cannot login to internal app (SSO error).",
                "details": "Several users report 'invalid SAML response'. Started ~20 minutes ago.",
                "impact": "high",
                "urgency": "high",
            },
        )
        created = json.loads(created_resp.content[0].text)
        print(json.dumps(created, indent=2))

        print("\n=== Read research plan resource ===")
        plan = await client.read_resource(created["resource_uri"])
        print(plan[0].text)

        print("\n=== Get prompt: ask_clarifying_questions ===")
        prompt = await client.get_prompt(
            "ask_clarifying_questions",
            {"category": pack["incident"]["category"], "severity": pack["incident"]["severity"]},
        )
        for i, msg in enumerate(prompt.messages, start=1):
            print(f"\n--- Prompt message {i} ({msg.role}) ---")
            print(msg.content)


if __name__ == "__main__":
    asyncio.run(main())
