from __future__ import annotations

from io import BytesIO

from app.services.policy_corpus import ParsedClause, parse_policy_clauses_from_pages


def test_parse_policy_clauses_from_pages_uses_stable_clause_ids() -> None:
    pages = [
        (
            1,
            "\n".join(
                [
                    "1.1 Coverage",
                    "Water pump failures are covered under standard warranty.",
                    "1.2 Exclusions",
                    "Damage caused by abuse is excluded.",
                ]
            ),
        )
    ]

    clauses = parse_policy_clauses_from_pages(pages, policy_code="POWERTRAIN", version="2026")

    assert len(clauses) == 2
    assert clauses[0].clause_id == "POWERTRAIN-2026-1.1"
    assert clauses[0].title == "Coverage"
    assert "Water pump failures" in clauses[0].clause_text
    assert clauses[1].clause_id == "POWERTRAIN-2026-1.2"


def test_upload_policy_corpus_and_retrieve_clauses(client, monkeypatch) -> None:
    parsed = [
        ParsedClause(
            policy_id="POWERTRAIN-2026",
            clause_id="POWERTRAIN-2026-4.2",
            section="4.2",
            title="Cooling System Coverage",
            clause_text="Water pump failures are covered when no exclusion applies.",
            clause_link="POWERTRAIN-2026#4.2",
            page_number=4,
            retrieval_terms="4.2 Cooling System Coverage Water pump failures are covered when no exclusion applies.",
        ),
        ParsedClause(
            policy_id="POWERTRAIN-2026",
            clause_id="POWERTRAIN-2026-7.1",
            section="7.1",
            title="Exclusions",
            clause_text="Unauthorized modification and abuse are excluded.",
            clause_link="POWERTRAIN-2026#7.1",
            page_number=7,
            retrieval_terms="7.1 Exclusions Unauthorized modification and abuse are excluded.",
        ),
    ]

    monkeypatch.setattr("app.services.policy_corpus.parse_policy_pdf", lambda *_args, **_kwargs: parsed)

    upload_response = client.post(
        "/policy-corpus/upload",
        files={"file": ("policy.pdf", b"%PDF-1.4 fake pdf bytes", "application/pdf")},
        data={
            "policy_name": "Powertrain",
            "policy_type": "Warranty",
            "version": "2026",
            "effective_date": "2026-01-01",
        },
    )

    assert upload_response.status_code == 200
    upload_body = upload_response.json()
    assert upload_body["policy_id"] == "POWERTRAIN-2026"
    assert upload_body["clause_count"] == 2

    retrieve_response = client.post(
        "/policy-corpus/retrieve",
        json={"query": "water pump coverage", "policy_id": "POWERTRAIN-2026", "top_k": 5},
    )

    assert retrieve_response.status_code == 200
    retrieve_body = retrieve_response.json()
    assert retrieve_body["count"] >= 1
    assert retrieve_body["clauses"][0]["clause_id"] == "POWERTRAIN-2026-4.2"

    list_response = client.get("/policy-corpus/POWERTRAIN-2026/clauses")
    assert list_response.status_code == 200
    listed_clauses = list_response.json()
    assert len(listed_clauses) == 2
