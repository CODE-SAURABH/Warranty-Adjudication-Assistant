from __future__ import annotations

from app.services import agent_tools


def test_search_policy_clauses_falls_back_to_legacy_clauses(monkeypatch) -> None:
    monkeypatch.setattr(agent_tools, "search_policy_corpus_clauses", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(
        agent_tools,
        "load_policy_clauses",
        lambda *_args, **_kwargs: [
            {
                "id": 1,
                "source_name": "clauses.json",
                "clause_id": "4.2",
                "section": "Cooling System Coverage",
                "clause_quote": "Water pump failures are covered when no exclusion applies.",
            }
        ],
    )

    response = agent_tools.search_policy_clauses("water pump coverage", policy_id="WRTY-PWR-001", top_k=5)

    assert response["retrieval_source"] == "legacy_policy_clause_db"
    assert response["count"] == 1
    assert response["clauses"][0]["clause_id"] == "4.2"
    assert response["clauses"][0]["clause_quote"] == "Water pump failures are covered when no exclusion applies."


def test_get_policy_clauses_by_ids_falls_back_to_legacy_clauses(monkeypatch) -> None:
    monkeypatch.setattr(agent_tools, "load_policy_corpus_clauses_by_ids", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(
        agent_tools,
        "load_policy_clauses",
        lambda *_args, **_kwargs: [
            {
                "id": 1,
                "source_name": "clauses.json",
                "clause_id": "7.1",
                "section": "Exclusions",
                "clause_quote": "Damage caused by abuse is excluded.",
            }
        ],
    )

    response = agent_tools.get_policy_clauses_by_ids("WRTY-PWR-001", ["7.1"])

    assert response["retrieval_source"] == "legacy_policy_clause_db"
    assert response["count"] == 1
    assert response["clauses"][0]["clause_link"] == "clauses.json#7.1"


def test_save_claim_decision_backfills_claim_id_from_assessor_queue(monkeypatch) -> None:
    captured_payload = {}

    def fake_save(payload):
        captured_payload.update(payload)
        return {"id": 99, "claim_id": payload["claim_id"], "disposition": payload["disposition_per_claim"]["decision"]}

    monkeypatch.setattr(agent_tools, "save_claim_decision_record", fake_save)

    response = agent_tools.save_claim_decision(
        {
            "disposition_per_claim": {"decision": "APPROVE", "confidence": 0.91},
            "cited_justification": [],
            "missing_information": [],
            "assessor_ui": {
                "claim_queue": {
                    "claim_id": "CLM-TEST-001",
                    "recommended_action": "APPROVE",
                    "priority": "NORMAL",
                },
                "decision_detail": {
                    "summary": "Approved after adjudication.",
                    "rule_summary": "All checks passed.",
                    "flags": [],
                    "citations": [],
                },
                "override_capability": {
                    "allowed": True,
                    "required_fields": ["assessor_decision", "assessor_rationale"],
                    "audit_message": "Override rationale must be logged.",
                },
            },
        }
    )

    assert captured_payload["claim_id"] == "CLM-TEST-001"
    assert response["saved"] is True
    assert response["claim_id"] == "CLM-TEST-001"
