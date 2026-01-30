#!/usr/bin/env python3
"""
ITSM MCP Server (Simplified for MCP Labs)

Goal:
- Teach MCP with realistic enterprise examples without too many moving parts.

This server demonstrates:
1) A "non-text" tool that returns a machine-usable incident pack:
   - normalized fields (severity/category)
   - recommended next steps
   - suggested KB resource URIs to fetch via read_resource()
2) A tool that creates an artifact and returns a resource URI:
   - create_research_plan -> itsm://cases/<id>/research-plan
3) Resources:
   - incident severity policy
   - KB articles
4) A prompt template:
   - ask_clarifying_questions
5) Basic audit logging to JSONL.

Transport:
- Streamable HTTP (FastMCP "http")
"""

from __future__ import annotations

import json
import os
import time
import uuid
from typing import Any, Dict, List, Literal, Optional, Tuple

from fastmcp import FastMCP
from fastmcp.prompts import Message
from starlette.requests import Request
from starlette.responses import PlainTextResponse


AUDIT_LOG = os.getenv("ITSM_AUDIT_LOG", "./itsm_audit.jsonl")
mcp = FastMCP(name="ITSM Service Desk (Enterprise) - Simplified")

# In-memory store for lab purposes (not durable).
_CASE_STORE: Dict[str, Dict[str, Any]] = {}


def _now_ms() -> int:
    return int(time.time() * 1000)


def _audit(event_type: str, payload: Dict[str, Any]) -> None:
    record = {"ts_ms": _now_ms(), "event_type": event_type, "payload": payload}
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _norm(s: str) -> str:
    return (s or "").strip().lower()


def _severity_from_impact_urgency(impact: str, urgency: str) -> Literal["low", "medium", "high", "critical"]:
    impact = _norm(impact)
    urgency = _norm(urgency)

    if impact == "high" and urgency == "high":
        return "critical"
    if (impact == "high" and urgency in ("medium", "low")) or (urgency == "high" and impact in ("medium", "low")):
        return "high"
    if impact == "medium" and urgency == "medium":
        return "medium"
    return "low"


def _category_guess(text: str) -> str:
    t = (text or "").lower()
    if any(k in t for k in ["vpn", "wifi", "network", "dns", "latency", "packet loss"]):
        return "network"
    if any(k in t for k in ["login", "sso", "oauth", "saml", "password", "mfa", "2fa"]):
        return "identity_access"
    if any(k in t for k in ["kubernetes", "k8s", "docker", "container", "pod", "deployment"]):
        return "platform"
    if any(k in t for k in ["email", "outlook", "exchange", "mailbox"]):
        return "email_collaboration"
    return "general"


def _triage_next_steps(category: str, severity: str) -> List[str]:
    """
    Small, teachable list: 3–4 steps.
    """
    cat = _norm(category)
    sev = _norm(severity)

    base = [
        "Confirm scope (how many users/regions) and exact start time",
        "Capture exact error message(s) + timestamps",
        "Check monitoring/status for related service health",
    ]
    if cat == "identity_access":
        base.append("Check IdP logs and recent SSO config/cert changes")
    elif cat == "network":
        base.append("Check VPN/DNS health and region-specific impact")
    elif cat == "platform":
        base.append("Check recent deploys and service error-rate/latency graphs")
    else:
        base.append("Identify any recent changes and known workarounds")

    if sev in ("critical", "high"):
        base.insert(0, "Start incident bridge and assign an incident commander (IC)")

    return base[:4]


def _kb_catalog() -> Dict[str, Dict[str, Any]]:
    """
    Minimal KB metadata used for suggesting KB resource URIs.
    """
    return {
        "kb-1001": {
            "title": "VPN Troubleshooting",
            "tags": ["vpn", "network", "connectivity"],
            "categories": ["network"],
        },
        "kb-2001": {
            "title": "SSO Login Failures",
            "tags": ["sso", "saml", "oauth", "mfa", "login"],
            "categories": ["identity_access"],
        },
        "kb-3001": {
            "title": "Password Reset (Standard)",
            "tags": ["password", "login", "mfa"],
            "categories": ["identity_access"],
        },
    }


def _rank_kb(category: str, query_text: str, max_results: int) -> List[str]:
    cat = _norm(category)
    q = (query_text or "").lower()
    catalog = _kb_catalog()

    scored: List[Tuple[str, int]] = []
    for aid, meta in catalog.items():
        score = 0
        if cat in meta.get("categories", []):
            score += 3
        for tag in meta.get("tags", []):
            if tag in q:
                score += 2
        if meta.get("title", "").lower() in q:
            score += 1
        scored.append((aid, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    top = [aid for aid, s in scored if s > 0][: max(1, min(max_results, 10))]
    return top


def _build_research_plan(category: str, severity: str, short_description: str, details: str) -> Dict[str, Any]:
    category = _norm(category)
    severity = _norm(severity)
    context = f"{short_description}\n{details}".strip()

    if category == "identity_access":
        hypotheses = [
            "Identity provider issue or outage",
            "Recent SSO config/cert change",
            "Clock skew causing token validity failures",
        ]
        checks = [
            "Check IdP status + auth error patterns",
            "Review recent SSO changes (SAML/OAuth/certs)",
            "Validate time sync (NTP) for key systems",
        ]
        evidence = [
            "Exact error text + timestamps + impacted app URL",
            "Auth log excerpts and request IDs if available",
            "List of affected users/groups/regions",
        ]
    elif category == "network":
        hypotheses = ["Regional ISP issue", "VPN gateway saturation", "DNS issue"]
        checks = ["Check network dashboards", "Compare affected vs unaffected regions", "Validate DNS resolution paths"]
        evidence = ["Traceroute/ping from affected users", "VPN gateway metrics", "Time window + location map"]
    elif category == "platform":
        hypotheses = ["Recent deploy regression", "Dependency outage", "Resource exhaustion"]
        checks = ["Review recent deploys", "Check service metrics/logs", "Verify dependencies health"]
        evidence = ["Service logs around onset", "Dashboard screenshots", "Deployment IDs/change records"]
    else:
        hypotheses = ["Misconfiguration", "Transient outage", "User-specific issue"]
        checks = ["Confirm scope/timeframe", "Check status dashboards", "Review recent changes"]
        evidence = ["Error text + timestamps", "User/device context", "Steps already tried"]

    if severity in ("critical", "high"):
        checks.insert(0, "Start incident bridge and establish comms cadence")
        evidence.insert(0, "Business impact summary + blast radius estimate")

    return {
        "category": category,
        "severity": severity,
        "incident_context": context,
        "hypotheses": hypotheses,
        "checks": checks,
        "evidence_to_collect": evidence,
        "note": "Guidance only. Follow your org’s incident process.",
    }


@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")


@mcp.tool
def incident_pack(
    short_description: str,
    details: str,
    impact: Literal["low", "medium", "high"],
    urgency: Literal["low", "medium", "high"],
    customer_impacting: bool = False,
    max_kb_results: int = 3,
) -> Dict[str, Any]:
    """
    Returns a machine-usable incident bundle (not just prose):
    - severity/category/summary
    - next steps
    - suggested KB resource URIs to fetch via read_resource()
    - references to policy resources
    """
    severity = _severity_from_impact_urgency(impact, urgency)
    category = _category_guess(f"{short_description}\n{details}")

    should_escalate = bool(customer_impacting or severity in ("critical", "high"))
    kb_ids = _rank_kb(category=category, query_text=f"{short_description}\n{details}", max_results=max_kb_results)

    pack = {
        "incident": {
            "summary": short_description.strip(),
            "category": category,
            "severity": severity,
            "customer_impacting": customer_impacting,
            "escalation_hint": "Escalate to on-call" if should_escalate else "Handle in service desk queue",
        },
        "next_steps": _triage_next_steps(category=category, severity=severity),
        "resources": {
            "policy_uris": ["itsm://policies/incident-severity"],
            "kb_uris": [f"itsm://kb/{aid}" for aid in kb_ids],
        },
        "notes": "Client should fetch any URIs it wants via read_resource() and include in the prompt/context.",
    }

    _audit(
        "incident_pack",
        {
            "inputs": {
                "short_description": short_description,
                "impact": impact,
                "urgency": urgency,
                "customer_impacting": customer_impacting,
            },
            "result": pack,
        },
    )
    return pack


@mcp.tool
def create_research_plan(
    short_description: str,
    details: str,
    category: Optional[str] = None,
    severity: Optional[Literal["low", "medium", "high", "critical"]] = None,
    impact: Optional[Literal["low", "medium", "high"]] = None,
    urgency: Optional[Literal["low", "medium", "high"]] = None,
) -> Dict[str, Any]:
    """
    Create a research plan artifact and return a resource URI:
      itsm://cases/<case_id>/research-plan
    """
    inferred_category = category or _category_guess(f"{short_description}\n{details}")

    if severity:
        sev = _norm(severity)
    elif impact and urgency:
        sev = _severity_from_impact_urgency(impact, urgency)
    else:
        sev = "medium"

    case_id = f"CASE-{uuid.uuid4().hex[:10].upper()}"
    plan = _build_research_plan(
        category=inferred_category,
        severity=sev,
        short_description=short_description,
        details=details,
    )

    _CASE_STORE[case_id] = {
        "case_id": case_id,
        "created_ts_ms": _now_ms(),
        "short_description": short_description,
        "details": details,
        "plan": plan,
    }

    resource_uri = f"itsm://cases/{case_id}/research-plan"
    result = {
        "case_id": case_id,
        "resource_uri": resource_uri,
        "category": inferred_category,
        "severity": sev,
        "summary": "Research plan created. Fetch it via read_resource(resource_uri).",
    }
    _audit("create_research_plan", {"inputs": {"short_description": short_description}, "result": result})
    return result


@mcp.resource("itsm://policies/incident-severity")
def incident_severity_policy() -> str:
    return """# Incident Severity Policy (Snapshot)

- Critical: major service down / widespread customer impact / safety or compliance risk
- High: significant degradation or many users impacted
- Medium: limited impact, workaround exists
- Low: minor issue or single user impact

Always follow your org’s paging + incident commander rules for High/Critical.
"""


@mcp.resource("itsm://kb/{article_id}")
def kb_article(article_id: str) -> str:
    """
    Tiny KB resource stub. In a real setup, this would query ServiceNow KB, Confluence, etc.
    """
    aid = _norm(article_id)
    kb = {
        "kb-1001": "KB-1001: VPN Troubleshooting\n- Confirm VPN client version\n- Collect logs\n- Check known outages\n",
        "kb-2001": "KB-2001: SSO Login Failures\n- Check IdP status\n- Confirm MFA method\n- Verify app SAML config changes\n",
        "kb-3001": "KB-3001: Password Reset (Standard)\n- Verify identity\n- Reset via IAM portal\n- Confirm enrollment in MFA\n",
    }
    return kb.get(aid, f"No KB article found for {article_id}.")


@mcp.resource("itsm://cases/{case_id}/research-plan")
def case_research_plan(case_id: str) -> str:
    """
    Read the research plan for a previously created case.
    Lab simplicity: uses in-memory storage.
    """
    cid = (case_id or "").strip()
    entry = _CASE_STORE.get(cid)
    if not entry:
        return f"No research plan found for case_id={case_id}. Create one via tool create_research_plan()."

    plan = entry.get("plan", {})
    return (
        f"# Research Plan: {cid}\n\n"
        f"## Context\n{plan.get('incident_context','')}\n\n"
        f"## Category / Severity\n- Category: {plan.get('category','')}\n- Severity: {plan.get('severity','')}\n\n"
        f"## Hypotheses\n" + "\n".join(f"- {h}" for h in plan.get("hypotheses", [])) + "\n\n"
        f"## Checks\n" + "\n".join(f"- {c}" for c in plan.get("checks", [])) + "\n\n"
        f"## Evidence to Collect\n" + "\n".join(f"- {e}" for e in plan.get("evidence_to_collect", [])) + "\n\n"
        f"## Note\n{plan.get('note','')}\n"
    )


@mcp.prompt
def ask_clarifying_questions(category: str, severity: str) -> List[Message]:
    system = Message(
        "You are an IT Service Desk assistant. Ask only the minimum clarifying questions needed "
        "to triage and resolve. Keep questions short and numbered.",
        role="system",
    )
    user = Message(
        f"""Generate clarifying questions for:
Category: {category}
Severity: {severity}

Ask about:
1) Scope (# users, locations)
2) Exact error messages
3) Timeframe (when it started)
4) Recent changes
5) What has been tried already
""",
        role="user",
    )
    return [system, user]


if __name__ == "__main__":
    # Streamable HTTP transport
    # MCP endpoint: http://localhost:8000/mcp
    mcp.run(transport="http", host="127.0.0.1", port=8000)
