from __future__ import annotations

import asyncio
import copy
import json
import re
from typing import Any

from ..core.agents import create_agent, get_agent_client
from ..schemas.database import AdjudicationUiResponseSchema
from .agent_tools import (
    get_policy_clauses_by_ids,
    get_component_rule_by_repair_code,
    get_labor_cost_rule_by_id,
    get_prior_repair_history_by_ids,
    get_service_history_by_vin,
    get_warranty_product_by_id,
    retrieve_policy_clauses,
    search_policy_clauses,
    save_claim_decision,
)
from .rule_engine import run_rule_engine


FAILURE_DESCRIPTION_INJECTION_PATTERNS = (
    re.compile(r"\b(ignore|forget|disregard)\b.{0,60}\b(instruction|instructions|rule|rules|prompt|prompts)\b", re.IGNORECASE),
    re.compile(r"\bjust\s+say\b", re.IGNORECASE),
    re.compile(r"\bapprove(?:d)?\s+claim\b", re.IGNORECASE),
    re.compile(r"\bact\s+as\b", re.IGNORECASE),
    re.compile(r"\boverride\b.{0,40}\b(instruction|rule|decision)\b", re.IGNORECASE),
    re.compile(r"\bjailbreak\b", re.IGNORECASE),
)
SANITIZED_FAILURE_DESCRIPTION_NOTICE = "[Instruction-like content removed before agent adjudication.]"


AGENT_SYSTEM_PROMPT = """You are the assessor-facing Warranty Adjudication Agent for Vantara Commercial Vehicles.
You receive the deterministic backend rule-engine payload first and must turn it into the final claim decision pack for the UI.

Rules:
- Treat the rule engine as authoritative for gateway validation, coverage window checks, mileage checks, flags, and computed values.
- Never return an uncited decision. Every approve, reject, or refer recommendation must cite policy clauses retrieved with tools in this run.
- Search uploaded policy corpora with clause-aware retrieval when deterministic references are insufficient, and cite only real returned clause IDs.
- If coverage, exclusions, component mapping, labor thresholds, or prior-repair risks need context, use the available tools before deciding.
- If the rule engine recommends REJECT or REFER_TO_HUMAN due to a blocking business-rule failure, do not override it to APPROVE.
- A VIN cannot be approved for the same causal part more than 3 times. If prior repair history shows 3 or more earlier claims for the same causal part, or the rule engine flags SAME_PART_CLAIM_LIMIT_EXCEEDED, the decision must remain REJECT.
- If information is missing, explain exactly what is missing and cite the clause requiring it.
- Keep the output compact and JSON-only.

Return JSON with exactly this shape:
{
  "disposition_per_claim": {
    "decision": "APPROVE|REJECT|REFER_TO_HUMAN",
    "confidence": 0.0
  },
  "cited_justification": [
    {
      "clause_id": "string",
      "clause_quote": "string",
      "clause_link": "string",
      "justification": "string"
    }
  ],
  "missing_information": [
    {
      "item": "string",
      "message": "string",
      "required_clause_id": "string",
      "required_clause_quote": "string",
      "required_clause_link": "string"
    }
  ],
  "assessor_ui": {
    "claim_queue": {
      "claim_id": "string",
      "recommended_action": "APPROVE|REJECT|REFER_TO_HUMAN",
      "priority": "NORMAL|HIGH"
    },
    "decision_detail": {
      "summary": "string",
      "rule_summary": "string",
      "flags": ["string"],
      "citations": [
        {
          "clause_id": "string",
          "clause_link": "string"
        }
      ]
    },
    "override_capability": {
      "allowed": true,
      "required_fields": ["assessor_decision", "assessor_rationale"],
      "audit_message": "Override rationale must be logged."
    }
  }
}
"""


def create_warranty_adjudication_agent():
    return create_agent(
        name="Warranty Adjudication Agent",
        instructions=AGENT_SYSTEM_PROMPT,
        client=get_agent_client(),
    )


def _sanitize_failure_description_for_agent(value: Any) -> tuple[str, bool]:
    if not isinstance(value, str):
        return "", False

    text = re.sub(r"\s+", " ", value).strip()
    if not text:
        return "", False

    segments = re.split(r"(?<=[.!?])\s+", text)
    safe_segments: list[str] = []
    removed_segments = 0

    for segment in segments:
        cleaned = segment.strip()
        if not cleaned:
            continue
        if any(pattern.search(cleaned) for pattern in FAILURE_DESCRIPTION_INJECTION_PATTERNS):
            removed_segments += 1
            continue
        safe_segments.append(cleaned)

    if removed_segments == 0:
        return text, False

    sanitized = " ".join(safe_segments).strip()
    if sanitized:
        return f"{sanitized} {SANITIZED_FAILURE_DESCRIPTION_NOTICE}", True
    return SANITIZED_FAILURE_DESCRIPTION_NOTICE, True


def _sanitize_rule_engine_result_for_agent(rule_engine_result: dict[str, Any]) -> dict[str, Any]:
    sanitized_payload = copy.deepcopy(rule_engine_result)
    claim = sanitized_payload.get("claim")
    if not isinstance(claim, dict):
        return sanitized_payload

    sanitized_failure_description, was_sanitized = _sanitize_failure_description_for_agent(
        claim.get("failure_description")
    )
    if not was_sanitized:
        return sanitized_payload

    claim["failure_description"] = sanitized_failure_description
    sanitized_payload["agent_input_safety"] = {
        "failure_description_sanitized": True,
        "reason": "Instruction-like text was removed from failure_description before the payload reached the agent.",
    }
    return sanitized_payload


def _build_agent_prompt(rule_engine_result: dict[str, Any]) -> str:
    sanitized_rule_engine_result = _sanitize_rule_engine_result_for_agent(rule_engine_result)
    return (
        "Review the deterministic warranty rule-engine payload below and produce the final assessor-facing JSON in the required schema.\n"
        "Use tools for citations and flagged context, and do not return an uncited decision.\n\n"
        f"{json.dumps(sanitized_rule_engine_result, indent=2)}"
    )


def _strip_json_fence(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned


def _parse_agent_response_text(text: str) -> dict[str, Any]:
    cleaned = _strip_json_fence(text)
    return json.loads(cleaned)


def _normalize_agent_output(rule_engine_result: dict[str, Any], agent_output: dict[str, Any]) -> dict[str, Any]:
    is_clean_approval_case = (
        rule_engine_result.get("gateway_status") == "CONTINUE"
        and rule_engine_result.get("overall_rule_status") == "PASS"
        and rule_engine_result.get("recommended_disposition") == "CONTINUE"
        and not rule_engine_result.get("failed_checks")
        and not rule_engine_result.get("warnings")
        and not rule_engine_result.get("missing_info")
        and not rule_engine_result.get("flags")
    )

    if not is_clean_approval_case:
        return agent_output

    disposition = agent_output.setdefault("disposition_per_claim", {})
    disposition["decision"] = "APPROVE"

    assessor_ui = agent_output.setdefault("assessor_ui", {})
    claim_queue = assessor_ui.setdefault("claim_queue", {})
    claim_queue["claim_id"] = rule_engine_result.get("claim_id")
    claim_queue["recommended_action"] = "APPROVE"
    claim_queue.setdefault("priority", "NORMAL")

    decision_detail = assessor_ui.setdefault("decision_detail", {})
    decision_detail["rule_summary"] = rule_engine_result.get("rule_summary", "")
    decision_detail["flags"] = []
    if not decision_detail.get("summary"):
        decision_detail["summary"] = "Claim passed all deterministic warranty checks and is recommended for approval."

    agent_output["missing_information"] = []
    return agent_output


def extract_ui_adjudication_response(
    agent_output: dict[str, Any],
    *,
    fallback_claim_id: str | None = None,
) -> dict[str, Any]:
    claim_id = str(agent_output.get("claim_id", "")).strip()
    if not claim_id:
        claim_queue = agent_output.get("assessor_ui")
        if isinstance(claim_queue, dict):
            claim_queue = claim_queue.get("claim_queue")
        if isinstance(claim_queue, dict):
            claim_id = str(claim_queue.get("claim_id", "")).strip()
    if not claim_id:
        claim_id = str(fallback_claim_id or "").strip()

    assessor_ui = agent_output.get("assessor_ui", {}) if isinstance(agent_output.get("assessor_ui"), dict) else {}
    override_capability = (
        assessor_ui.get("override_capability", {})
        if isinstance(assessor_ui.get("override_capability"), dict)
        else {}
    )

    ui_payload = {
        "claim_id": claim_id,
        "disposition_per_claim": agent_output.get("disposition_per_claim", {}),
        "cited_justification": agent_output.get("cited_justification", []),
        "missing_information": agent_output.get("missing_information", []),
        "assessor_ui": {
            "claim_queue": assessor_ui.get("claim_queue", {}),
            "decision_detail": assessor_ui.get("decision_detail", {}),
            "override_capability": {
                "allowed": override_capability.get("allowed", False),
                "required_fields": override_capability.get("required_fields", []),
            },
        },
    }
    return AdjudicationUiResponseSchema.model_validate(ui_payload).model_dump()


async def run_adjudication_agent_async(rule_engine_result: dict[str, Any]) -> dict[str, Any]:
    agent = create_warranty_adjudication_agent()
    prompt = _build_agent_prompt(rule_engine_result)
    result = await agent.run(
        prompt,
        tools=[
            retrieve_policy_clauses,
            search_policy_clauses,
            get_policy_clauses_by_ids,
            get_prior_repair_history_by_ids,
            get_service_history_by_vin,
            get_warranty_product_by_id,
            get_component_rule_by_repair_code,
            get_labor_cost_rule_by_id,
            save_claim_decision,
        ],
    )
    return _normalize_agent_output(rule_engine_result, _parse_agent_response_text(result.text))


def run_adjudication_agent(rule_engine_result: dict[str, Any]) -> dict[str, Any]:
    return asyncio.run(run_adjudication_agent_async(rule_engine_result))


async def adjudicate_claim_async(claim: dict[str, Any]) -> dict[str, Any]:
    rule_engine_output = run_rule_engine(claim)

    try:
        agent_output = await run_adjudication_agent_async(rule_engine_output)
    except Exception as exc:
        agent_output = {
            "disposition_per_claim": {
                "decision": "REFER_TO_HUMAN",
                "confidence": 0.0,
            },
            "cited_justification": [],
            "missing_information": [],
            "assessor_ui": {
                "claim_queue": {
                    "claim_id": rule_engine_output.get("claim_id"),
                    "recommended_action": "REFER_TO_HUMAN",
                    "priority": "HIGH",
                },
                "decision_detail": {
                    "summary": "Agent adjudication could not be completed.",
                    "rule_summary": rule_engine_output.get("rule_summary", ""),
                    "flags": sorted(set((rule_engine_output.get("flags") or []) + ["AGENT_EXECUTION_ERROR"])),
                    "citations": [],
                },
                "override_capability": {
                    "allowed": True,
                    "required_fields": ["assessor_decision", "assessor_rationale"],
                    "audit_message": f"Agent fallback triggered: {exc}",
                },
            },
            "error": str(exc),
        }

    return {
        "rule_engine_output": rule_engine_output,
        "agent_output": agent_output,
    }


def adjudicate_claim(claim: dict[str, Any]) -> dict[str, Any]:
    return asyncio.run(adjudicate_claim_async(claim))
