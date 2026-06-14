from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from ..core.config import settings
from ..repositories.database_store import load_reference_snapshot

DATA_DIR = settings.data_dir
DATE_FORMAT = "%Y-%m-%d"
FAILURE_SECTION_PATTERNS = {
    "complaint": [
        re.compile(r"\bcomplaint\s*:", re.IGNORECASE),
        re.compile(r"\bcustomer complaint\s*:", re.IGNORECASE),
    ],
    "cause": [
        re.compile(r"\bcause\s*:", re.IGNORECASE),
        re.compile(r"\broot cause\s*:", re.IGNORECASE),
    ],
    "correction": [
        re.compile(r"\bcorrection\s*:", re.IGNORECASE),
        re.compile(r"\brepair performed\s*:", re.IGNORECASE),
    ],
}
EXCLUSION_KEYWORDS = [
    "abuse",
    "racing",
    "track use",
    "unauthorized modification",
    "tuned ecu",
    "collision",
    "accident",
    "contaminated coolant",
    "contaminated fluid",
    "lack of maintenance",
    "normal wear",
]
DATA_FILES = {
    "masterCustomerdata": "masterCustomerdata.json",
    "warrantydata": "warrantydata.json",
    "customerWarrantydata": "customerWarrantydata.json",
    "components": "components.json",
    "laborAndCostRules": "laborAndCostRules.json",
    "priorRepairHistory": "priorRepairHistory.json",
    "serviceHistory": "serviceHistory.json",
}


def load_json_file(file_name: str) -> Any:
    path = DATA_DIR / file_name
    if not path.exists():
        raise FileNotFoundError(f"Missing data file: {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"Malformed JSON in {path}: {exc}") from exc


def generate_claim_id() -> str:
    return datetime.utcnow().strftime("CLM-%Y%m%d-%H%M%S")


def parse_date(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except ValueError:
        return None


def find_customer_by_vin(vin: str, data: dict[str, Any]) -> dict[str, Any] | None:
    return next((item for item in data["masterCustomerdata"] if item.get("vin") == vin), None)


def find_warranty_mappings_by_vin(vin: str, data: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in data["customerWarrantydata"] if item.get("vin") == vin]


def find_warranty_product_by_id(warranty_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
    return next((item for item in data["warrantydata"] if item.get("warranty_id") == warranty_id), None)


def find_component_rule(repair_code: Any, data: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(repair_code, str):
        return None
    return next((item for item in data["components"] if item.get("repair_code") == repair_code), None)


def find_labor_cost_rule(
    repair_code: str | None,
    warranty_id: str | None,
    repair_order_date: datetime | None,
    data: dict[str, Any],
) -> dict[str, Any] | None:
    if not repair_code or not warranty_id:
        return None
    candidates: list[dict[str, Any]] = []
    for rule in data["laborAndCostRules"]:
        if rule.get("repair_code") != repair_code or rule.get("warranty_id") != warranty_id:
            continue
        start = parse_date(rule.get("effective_from"))
        end = parse_date(rule.get("effective_to"))
        if repair_order_date and start and end and not (start <= repair_order_date <= end):
            continue
        candidates.append(rule)
    active = [rule for rule in candidates if rule.get("status") == "Active"]
    return (active or candidates or [None])[0]


def find_prior_repairs_by_vin(vin: str, data: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in data["priorRepairHistory"] if item.get("vin") == vin]


def find_service_history_by_vin(vin: str, data: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in data["serviceHistory"] if item.get("vin") == vin]


def contains_attachment(attachments: list[Any], *keywords: str) -> bool:
    normalized = [str(item).lower() for item in attachments]
    for attachment in normalized:
        if all(keyword.lower() in attachment for keyword in keywords):
            return True
    return False


def extract_failure_story_sections(failure_description: Any) -> dict[str, bool]:
    text = failure_description.strip() if isinstance(failure_description, str) else ""
    result = {"has_complaint": False, "has_cause": False, "has_correction": False}
    for key, patterns in FAILURE_SECTION_PATTERNS.items():
        result[f"has_{key}"] = any(pattern.search(text) for pattern in patterns)
    result["is_complete"] = all(result.values()) if any(result.values()) else bool(text)
    return result


def scan_exclusion_keywords(failure_description: Any) -> dict[str, Any]:
    text = failure_description.lower() if isinstance(failure_description, str) else ""
    found = [keyword for keyword in EXCLUSION_KEYWORDS if keyword in text]
    return {
        "keywords_found": found,
        "requires_agent_interpretation": bool(found),
    }


def calculate_rule_confidence(
    failed_checks: list[dict[str, str]] | None = None,
    warnings: list[dict[str, str]] | None = None,
) -> float:
    failed_checks = failed_checks or []
    warnings = warnings or []
    score = 0.99
    score -= 0.12 * len(failed_checks)
    score -= 0.03 * len(warnings)
    return round(max(0.2, min(0.99, score)), 2)


def _load_all_data() -> dict[str, Any]:
    snapshot = load_reference_snapshot()
    if all(snapshot.get(key) for key in DATA_FILES):
        return {key: snapshot[key] for key in DATA_FILES}
    return {key: load_json_file(file_name) for key, file_name in DATA_FILES.items()}


def _claim_view(claim: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "in_service_date": claim.get("in_service_date"),
        "repair_order_date": claim.get("repair_order_date"),
        "mileage_km": claim.get("mileage_km"),
        "repair_code": claim.get("repair_code"),
        "causal_part": claim.get("causal_part"),
        "parts_cost_eur": claim.get("parts_cost_eur"),
        "labor_hours": claim.get("labor_hours"),
        "failure_description": claim.get("failure_description"),
        "attachments": claim.get("attachments", []) if isinstance(claim.get("attachments"), list) else [],
    }
    if isinstance(claim.get("repair_codes"), list) and claim.get("repair_codes"):
        payload["repair_codes"] = claim.get("repair_codes")
    if isinstance(claim.get("causal_parts"), list) and claim.get("causal_parts"):
        payload["causal_parts"] = claim.get("causal_parts")
    return payload


def _base_validation_summary() -> dict[str, bool]:
    return {
        "vin_found": False,
        "warranty_resolved": False,
        "repair_date_within_warranty": False,
        "mileage_within_limit": False,
        "component_valid": False,
        "component_covered": False,
        "labor_valid": False,
        "cost_valid": False,
        "documents_valid": False,
        "duplicate_risk": False,
        "prior_repair_risk": False,
        "maintenance_compliance": False,
        "service_gap_risk": False,
        "service_history_complete": False,
        "mileage_anomaly": False,
        "exclusion_risk": False,
    }


def _base_computed() -> dict[str, float | int | None]:
    return {
        "labor_cost_eur": None,
        "total_claim_cost_eur": None,
        "warranty_days_remaining": None,
        "warranty_mileage_remaining_km": None,
    }


def _base_refs() -> dict[str, Any]:
    return {
        "customer_id": None,
        "warranty_mapping_id": None,
        "warranty_id": None,
        "clauses_doc_ref": None,
        "repair_code": None,
        "repair_codes": [],
        "component_group": None,
        "causal_parts": [],
        "labor_cost_rule_id": None,
        "prior_repair_history_ids": [],
        "service_history_ids": [],
    }


def _days_between(start: datetime, end: datetime) -> int:
    return (end - start).days


def _goodwill_percent(current: float, limit: float) -> float:
    if limit <= 0:
        return 0.0
    return round(((current - limit) / limit) * 100, 2)


def _is_mapping_cancelled(mapping: dict[str, Any]) -> bool:
    return str(mapping.get("status", "")).strip().lower() == "cancelled"


def _stored_status_is_stale(mapping: dict[str, Any], *, repair_order_date: datetime | None, mileage: float) -> bool:
    if repair_order_date is None:
        return False

    start = parse_date(mapping.get("start_date"))
    end = parse_date(mapping.get("end_date"))
    if not start or not end:
        return False

    within_date = start <= repair_order_date <= end
    within_mileage = mileage <= float(mapping.get("end_mileage_km", 0) or 0)
    normalized_status = str(mapping.get("status", "")).strip().lower()

    if within_date and within_mileage:
        return normalized_status not in {"active", ""}
    if repair_order_date > end or not within_mileage:
        return normalized_status == "active"
    return False


def _default_goodwill_precheck(reason: str = "No goodwill condition identified.") -> dict[str, Any]:
    return {
        "eligible": False,
        "reason": reason,
        "overage_type": "None",
        "overage_percent": 0.0,
    }


def _make_compact_result(
    claim: dict[str, Any],
    *,
    gateway_status: str,
    overall_rule_status: str,
    recommended_disposition: str,
    rule_confidence: float,
    rule_summary: str,
    refs: dict[str, Any] | None = None,
    computed: dict[str, Any] | None = None,
    validation_summary: dict[str, bool] | None = None,
    failed_checks: list[dict[str, str]] | None = None,
    warnings: list[dict[str, str]] | None = None,
    missing_info: list[dict[str, str]] | None = None,
    flags: list[str] | None = None,
    goodwill_precheck: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "claim_id": claim["claim_id"],
        "vin": claim.get("vin"),
        "gateway_status": gateway_status,
        "overall_rule_status": overall_rule_status,
        "recommended_disposition": recommended_disposition,
        "rule_confidence": rule_confidence,
        "rule_summary": rule_summary,
        "claim": _claim_view(claim),
        "refs": refs or _base_refs(),
        "computed": computed or _base_computed(),
        "validation_summary": validation_summary or _base_validation_summary(),
        "failed_checks": failed_checks or [],
        "warnings": warnings or [],
        "missing_info": missing_info or [],
        "flags": sorted(set(flags or [])),
        "goodwill_precheck": goodwill_precheck or _default_goodwill_precheck(),
    }


def _component_candidate_pairs(
    vin: str,
    claim: dict[str, Any],
    data: dict[str, Any],
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    component_rule = find_component_rule(claim.get("repair_code"), data)
    mappings = find_warranty_mappings_by_vin(vin, data)
    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for mapping in mappings:
        product = find_warranty_product_by_id(mapping.get("warranty_id"), data)
        if not product:
            continue
        if component_rule and component_rule.get("covered_under_warranty_ids"):
            if mapping.get("warranty_id") not in component_rule.get("covered_under_warranty_ids", []):
                continue
        pairs.append((mapping, product))
    if pairs:
        return pairs
    for mapping in mappings:
        product = find_warranty_product_by_id(mapping.get("warranty_id"), data)
        if product:
            pairs.append((mapping, product))
    return pairs


def _is_component_excluded(component_rule: dict[str, Any], warranty_product: dict[str, Any]) -> bool:
    causal_part = str(component_rule.get("causal_part", "")).lower()
    component_group = str(component_rule.get("component_group", "")).lower()
    repair_description = str(component_rule.get("repair_description", "")).lower()
    for excluded in warranty_product.get("excluded_parts", []):
        token = str(excluded).lower()
        if token and (token == causal_part or token in causal_part or token in component_group or token in repair_description):
            return True
    return False


def _gateway_terminal_result(
    claim: dict[str, Any],
    *,
    rule_summary: str,
    refs: dict[str, Any],
    computed: dict[str, Any],
    validation_summary: dict[str, bool],
    failed_checks: list[dict[str, str]],
    warnings: list[dict[str, str]],
    missing_info: list[dict[str, str]],
    flags: list[str],
    goodwill_precheck: dict[str, Any],
    recommended_disposition: str = "REJECT",
) -> dict[str, Any]:
    return _make_compact_result(
        claim,
        gateway_status="TERMINAL",
        overall_rule_status="BLOCKED",
        recommended_disposition=recommended_disposition,
        rule_confidence=calculate_rule_confidence(failed_checks, warnings),
        rule_summary=rule_summary,
        refs=refs,
        computed=computed,
        validation_summary=validation_summary,
        failed_checks=failed_checks,
        warnings=warnings,
        missing_info=missing_info,
        flags=flags,
        goodwill_precheck=goodwill_precheck,
    )


def _has_prior_approval(attachments: list[Any]) -> bool:
    return contains_attachment(attachments, "approval") or contains_attachment(attachments, "prior", "approval")


def _handle_threshold_breach(
    *,
    attachments: list[Any],
    warning_code: str,
    warning_message: str,
    missing_item: str,
    missing_message: str,
    warning_flag: str,
    missing_flag: str,
    warn_fn: Any,
    need_fn: Any,
) -> None:
    if _has_prior_approval(attachments):
        warn_fn(warning_code, warning_message, warning_flag)
    else:
        need_fn(missing_item, missing_message, missing_flag)


def _collect_prior_repair_signals(
    *,
    claim: dict[str, Any],
    component_rule: dict[str, Any] | None,
    prior_repairs: list[dict[str, Any]],
    repair_order_date: datetime | None,
    mileage: float,
) -> dict[str, Any]:
    duplicate_records: list[dict[str, Any]] = []
    repeat_repairs: list[dict[str, Any]] = []
    related_repairs: list[dict[str, Any]] = []
    same_part_claim_records: list[dict[str, Any]] = []
    mileage_anomaly = False

    for record in prior_repairs:
        record_date = parse_date(record.get("repair_order_date"))
        if not record_date or not repair_order_date:
            continue
        delta_days = _days_between(record_date, repair_order_date)
        if delta_days < 0:
            continue
        if float(record.get("mileage_km", 0) or 0) > mileage:
            mileage_anomaly = True
        if record.get("causal_part") == claim.get("causal_part") and str(record.get("disposition", "")).strip().upper() not in {"REJECT", "REJECTED"}:
            same_part_claim_records.append(record)
        if record.get("repair_code") == claim.get("repair_code") and record.get("causal_part") == claim.get("causal_part") and delta_days <= 30:
            duplicate_records.append(record)
        elif record.get("causal_part") == claim.get("causal_part") and delta_days <= 365:
            repeat_repairs.append(record)
        elif component_rule and record.get("component_group") == component_rule.get("component_group") and record.get("causal_part") != claim.get("causal_part"):
            related_repairs.append(record)

    return {
        "duplicate_records": duplicate_records,
        "repeat_repairs": repeat_repairs,
        "related_repairs": related_repairs,
        "same_part_claim_records": same_part_claim_records,
        "same_part_claim_count": len(same_part_claim_records),
        "mileage_anomaly": mileage_anomaly,
    }


def _collect_service_history_signals(
    *,
    vin: str,
    service_history: list[dict[str, Any]],
    repair_order_date: datetime | None,
    mileage: float,
) -> dict[str, Any]:
    relevant_records = [
        record
        for record in service_history
        if record.get("vin") == vin and record.get("service_status") in {"Completed", "Open", "Cancelled"}
    ]
    sorted_records = sorted(
        relevant_records,
        key=lambda record: (
            parse_date(record.get("service_date")) or datetime.min,
            float(record.get("mileage_km", 0) or 0),
        ),
    )
    completed_records = [record for record in sorted_records if record.get("service_status") == "Completed"]
    prior_completed_records = [
        record
        for record in completed_records
        if not repair_order_date or ((record_date := parse_date(record.get("service_date"))) and record_date <= repair_order_date)
    ]
    non_compliant_records = [
        record for record in prior_completed_records if str(record.get("maintenance_compliance", "")).lower() == "non-compliant"
    ]
    oem_gap_records = [record for record in prior_completed_records if not bool(record.get("is_oem_authorized_service"))]
    open_records = [record for record in sorted_records if record.get("service_status") == "Open"]
    cancelled_records = [record for record in sorted_records if record.get("service_status") == "Cancelled"]
    coolant_records = [
        record
        for record in prior_completed_records
        if "coolant" in str(record.get("service_type", "")).lower()
        or any("coolant" in str(item).lower() for item in (record.get("performed_items") or []))
        or any("coolant" in str(item).lower() for item in (record.get("fluids_replaced") or []))
    ]
    service_gap_detected = False
    mileage_anomaly = False
    for previous, current in zip(prior_completed_records, prior_completed_records[1:]):
        previous_date = parse_date(previous.get("service_date"))
        current_date = parse_date(current.get("service_date"))
        if previous_date and current_date and _days_between(previous_date, current_date) > 365:
            service_gap_detected = True
        if float(current.get("mileage_km", 0) or 0) < float(previous.get("mileage_km", 0) or 0):
            mileage_anomaly = True
    if any(float(record.get("mileage_km", 0) or 0) > mileage for record in prior_completed_records):
        mileage_anomaly = True

    return {
        "records": sorted_records,
        "prior_completed_records": prior_completed_records,
        "non_compliant_records": non_compliant_records,
        "oem_gap_records": oem_gap_records,
        "open_records": open_records,
        "cancelled_records": cancelled_records,
        "coolant_records": coolant_records,
        "service_gap_detected": service_gap_detected,
        "mileage_anomaly": mileage_anomaly,
        "service_history_complete": len(prior_completed_records) >= 3,
    }


def run_gateway_validation(claim: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
    validation_summary = _base_validation_summary()
    refs = _base_refs()
    computed = _base_computed()
    failed_checks: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    missing_info: list[dict[str, str]] = []
    flags: list[str] = []
    goodwill_precheck = _default_goodwill_precheck()

    vin = claim.get("vin")
    mileage = float(claim.get("mileage_km", 0) or 0)
    repair_order_date = parse_date(claim.get("repair_order_date"))
    customer = find_customer_by_vin(vin, data)

    if customer:
        validation_summary["vin_found"] = True
        refs["customer_id"] = customer.get("customer_id")
    else:
        failed_checks.append({"code": "VIN_NOT_FOUND", "message": "VIN was not found in master customer data."})
        flags.append("VIN_NOT_FOUND")
        return _gateway_terminal_result(
            claim,
            rule_summary="VIN could not be resolved to a customer vehicle record.",
            refs=refs,
            computed=computed,
            validation_summary=validation_summary,
            failed_checks=failed_checks,
            warnings=warnings,
            missing_info=missing_info,
            flags=flags,
            goodwill_precheck=goodwill_precheck,
        )

    pairs = _component_candidate_pairs(vin, claim, data)
    mappings = find_warranty_mappings_by_vin(vin, data)
    if not mappings:
        failed_checks.append({"code": "WARRANTY_MAPPING_NOT_FOUND", "message": "No warranty mapping was found for the VIN."})
        flags.append("NO_WARRANTY_MAPPING")
        return _gateway_terminal_result(
            claim,
            rule_summary="Warranty mapping could not be resolved for the VIN.",
            refs=refs,
            computed=computed,
            validation_summary=validation_summary,
            failed_checks=failed_checks,
            warnings=warnings,
            missing_info=missing_info,
            flags=flags,
            goodwill_precheck=goodwill_precheck,
        )

    if not pairs:
        refs["warranty_mapping_id"] = mappings[0].get("mapping_id")
        refs["warranty_id"] = mappings[0].get("warranty_id")
        failed_checks.append({"code": "WARRANTY_PRODUCT_NOT_FOUND", "message": "Warranty mapping exists but no warranty product could be resolved."})
        flags.append("WARRANTY_PRODUCT_NOT_FOUND")
        return _gateway_terminal_result(
            claim,
            rule_summary="Warranty product could not be resolved for the VIN mapping.",
            refs=refs,
            computed=computed,
            validation_summary=validation_summary,
            failed_checks=failed_checks,
            warnings=warnings,
            missing_info=missing_info,
            flags=flags,
            goodwill_precheck=goodwill_precheck,
        )

    non_cancelled = [(mapping, product) for mapping, product in pairs if not _is_mapping_cancelled(mapping)]
    if not non_cancelled:
        refs["warranty_mapping_id"] = pairs[0][0].get("mapping_id")
        refs["warranty_id"] = pairs[0][0].get("warranty_id")
        failed_checks.append({"code": "WARRANTY_CANCELLED", "message": "Resolved warranty mapping is cancelled."})
        flags.append("WARRANTY_CANCELLED")
        return _gateway_terminal_result(
            claim,
            rule_summary="Resolved warranty mapping is cancelled.",
            refs=refs,
            computed=computed,
            validation_summary=validation_summary,
            failed_checks=failed_checks,
            warnings=warnings,
            missing_info=missing_info,
            flags=flags,
            goodwill_precheck=goodwill_precheck,
        )

    selected_mapping: dict[str, Any] | None = None
    selected_product: dict[str, Any] | None = None
    goodwill_candidates: list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]] = []

    for mapping, product in non_cancelled:
        start = parse_date(mapping.get("start_date"))
        end = parse_date(mapping.get("end_date"))
        if not start or not end or not repair_order_date:
            continue
        within_date = start <= repair_order_date <= end
        within_mileage = mileage <= float(mapping.get("end_mileage_km", 0) or 0)

        if within_date and within_mileage:
            selected_mapping = mapping
            selected_product = product
            validation_summary["warranty_resolved"] = True
            validation_summary["repair_date_within_warranty"] = True
            validation_summary["mileage_within_limit"] = True
            break

        if repair_order_date > end:
            coverage_days = max(1, _days_between(start, end))
            over_days = max(0, _days_between(end, repair_order_date))
            overage_percent = round((over_days / coverage_days) * 100, 2)
            if overage_percent <= 10.0:
                goodwill_candidates.append(
                    (
                        mapping,
                        product,
                        {
                            "eligible": True,
                            "reason": "Warranty exceeds time limit by no more than 10 percent.",
                            "overage_type": "Date",
                            "overage_percent": overage_percent,
                        },
                    )
                )
        elif not within_mileage:
            limit = float(mapping.get("end_mileage_km", 0) or 0)
            overage_percent = _goodwill_percent(mileage, limit)
            if overage_percent <= 10.0:
                goodwill_candidates.append(
                    (
                        mapping,
                        product,
                        {
                            "eligible": True,
                            "reason": "Warranty exceeds mileage limit by no more than 10 percent.",
                            "overage_type": "Mileage",
                            "overage_percent": overage_percent,
                        },
                    )
                )

    if selected_mapping and selected_product:
        refs["warranty_mapping_id"] = selected_mapping.get("mapping_id")
        refs["warranty_id"] = selected_mapping.get("warranty_id")
        refs["clauses_doc_ref"] = selected_product.get("clauses_doc_ref")
        end = parse_date(selected_mapping.get("end_date"))
        if end and repair_order_date:
            computed["warranty_days_remaining"] = _days_between(repair_order_date, end)
        computed["warranty_mileage_remaining_km"] = float(selected_mapping.get("end_mileage_km", 0) or 0) - mileage
        goodwill_precheck = _default_goodwill_precheck("Claim is within active warranty limits.")
        if _stored_status_is_stale(selected_mapping, repair_order_date=repair_order_date, mileage=mileage):
            warnings.append(
                {
                    "code": "WARRANTY_STATUS_DATA_MISMATCH",
                    "message": "Stored warranty status did not match derived coverage dates and mileage; derived coverage was used.",
                }
            )
            flags.append("WARRANTY_STATUS_DATA_MISMATCH")
        return {
            "gateway_status": "CONTINUE",
            "warranty_mapping": selected_mapping,
            "warranty_product": selected_product,
            "refs": refs,
            "computed": computed,
            "validation_summary": validation_summary,
            "warnings": warnings,
            "flags": flags,
            "goodwill_precheck": goodwill_precheck,
        }

    if goodwill_candidates:
        mapping, product, goodwill_precheck = sorted(goodwill_candidates, key=lambda item: item[2]["overage_percent"])[0]
        refs["warranty_mapping_id"] = mapping.get("mapping_id")
        refs["warranty_id"] = mapping.get("warranty_id")
        refs["clauses_doc_ref"] = product.get("clauses_doc_ref")
        validation_summary["warranty_resolved"] = True
        failed_checks.append({"code": "GOODWILL_CANDIDATE", "message": "Claim is slightly outside warranty limits and qualifies for goodwill review."})
        flags.append("GOODWILL_CANDIDATE")
        return _gateway_terminal_result(
            claim,
            rule_summary="Claim is outside warranty limits but qualifies for goodwill precheck.",
            refs=refs,
            computed=computed,
            validation_summary=validation_summary,
            failed_checks=failed_checks,
            warnings=warnings,
            missing_info=missing_info,
            flags=flags,
            goodwill_precheck=goodwill_precheck,
            recommended_disposition="REFER_TO_HUMAN",
        )

    mapping, product = non_cancelled[0]
    refs["warranty_mapping_id"] = mapping.get("mapping_id")
    refs["warranty_id"] = mapping.get("warranty_id")
    refs["clauses_doc_ref"] = product.get("clauses_doc_ref")
    validation_summary["warranty_resolved"] = True

    start = parse_date(mapping.get("start_date"))
    end = parse_date(mapping.get("end_date"))
    validation_summary["repair_date_within_warranty"] = bool(start and end and repair_order_date and start <= repair_order_date <= end)
    validation_summary["mileage_within_limit"] = mileage <= float(mapping.get("end_mileage_km", 0) or 0)

    if not validation_summary["repair_date_within_warranty"]:
        failed_checks.append({"code": "DATE_OUT_OF_COVERAGE", "message": "Repair order date is outside the applicable warranty period."})
        flags.append("DATE_OUT_OF_COVERAGE")
    if not validation_summary["mileage_within_limit"]:
        failed_checks.append({"code": "MILEAGE_OUT_OF_COVERAGE", "message": "Vehicle mileage exceeds the applicable warranty limit."})
        flags.append("MILEAGE_OUT_OF_COVERAGE")

    return _gateway_terminal_result(
        claim,
        rule_summary="Gateway business-rule validation failed.",
        refs=refs,
        computed=computed,
        validation_summary=validation_summary,
        failed_checks=failed_checks,
        warnings=warnings,
        missing_info=missing_info,
        flags=flags,
        goodwill_precheck=goodwill_precheck,
    )


def run_full_claim_validation(
    claim: dict[str, Any],
    gateway_result: dict[str, Any],
    data: dict[str, Any],
) -> dict[str, Any]:
    validation_summary = gateway_result.get("validation_summary", _base_validation_summary())
    refs = gateway_result.get("refs", _base_refs())
    computed = gateway_result.get("computed", _base_computed())
    failed_checks: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    missing_info: list[dict[str, str]] = []
    flags: list[str] = list(gateway_result.get("flags", []))

    active_mapping = gateway_result["warranty_mapping"]
    warranty_product = gateway_result["warranty_product"]
    repair_order_date = parse_date(claim.get("repair_order_date"))
    mileage = float(claim.get("mileage_km", 0) or 0)
    attachments = claim.get("attachments", []) if isinstance(claim.get("attachments"), list) else []
    component_rule = find_component_rule(claim.get("repair_code"), data)
    refs["repair_code"] = claim.get("repair_code")
    refs["repair_codes"] = claim.get("repair_codes", []) if isinstance(claim.get("repair_codes"), list) else []
    refs["causal_parts"] = claim.get("causal_parts", []) if isinstance(claim.get("causal_parts"), list) else []

    def fail(code: str, message: str, flag: str | None = None) -> None:
        failed_checks.append({"code": code, "message": message})
        if flag:
            flags.append(flag)

    def warn(code: str, message: str, flag: str | None = None) -> None:
        warnings.append({"code": code, "message": message})
        if flag:
            flags.append(flag)

    def need(item: str, message: str, flag: str | None = None) -> None:
        missing_info.append({"item": item, "message": message})
        if flag:
            flags.append(flag)

    submitted_repair_codes = claim.get("repair_codes", []) if isinstance(claim.get("repair_codes"), list) else []
    submitted_causal_parts = claim.get("causal_parts", []) if isinstance(claim.get("causal_parts"), list) else []
    if len(submitted_repair_codes) > 1 or len(submitted_causal_parts) > 1:
        warn(
            "MULTI_REPAIR_LINE_INPUT",
            "Multiple repair codes or causal parts were submitted. Deterministic validation used the first aligned repair-code/causal-part pair.",
            "MULTI_REPAIR_LINE_INPUT",
        )

    if component_rule:
        refs["component_group"] = component_rule.get("component_group")
        validation_summary["component_valid"] = (
            component_rule.get("repair_code") == claim.get("repair_code")
            and component_rule.get("causal_part") == claim.get("causal_part")
            and bool(component_rule.get("component_group"))
        )
        if component_rule.get("causal_part") != claim.get("causal_part"):
            warn("REPAIR_CODE_PART_MISMATCH", "Repair code does not match the submitted causal part.", "REPAIR_CODE_PART_MISMATCH")
        if not component_rule.get("component_group"):
            fail("COMPONENT_GROUP_NOT_RESOLVED", "Component group could not be resolved for the repair code.", "COMPONENT_GROUP_MISSING")
    else:
        validation_summary["component_valid"] = False
        fail("REPAIR_CODE_NOT_FOUND", "Repair code was not found in components.json.", "REPAIR_CODE_NOT_FOUND")

    if component_rule:
        excluded = _is_component_excluded(component_rule, warranty_product)
        covered = active_mapping.get("warranty_id") in component_rule.get("covered_under_warranty_ids", [])
        validation_summary["component_covered"] = covered and not excluded
        if excluded:
            fail("COMPONENT_EXPLICITLY_EXCLUDED", "The component is explicitly excluded under the mapped warranty.", "COMPONENT_EXCLUDED")
        elif not covered:
            fail("COMPONENT_NOT_COVERED", "The component is not covered under the mapped warranty.", "COMPONENT_NOT_COVERED")

    labor_cost_rule = find_labor_cost_rule(
        claim.get("repair_code"),
        active_mapping.get("warranty_id"),
        repair_order_date,
        data,
    )
    if labor_cost_rule:
        refs["labor_cost_rule_id"] = labor_cost_rule.get("rule_id")
    else:
        warn("LABOR_COST_RULE_MISSING", "No labor and cost rule was found for the repair code and warranty combination.", "LABOR_COST_RULE_MISSING")

    labor_hours = claim.get("labor_hours")
    parts_cost = claim.get("parts_cost_eur")
    if isinstance(labor_hours, (int, float)) and labor_cost_rule:
        computed["labor_cost_eur"] = round(float(labor_hours) * float(labor_cost_rule.get("labor_rate_eur_per_hour", 0)), 2)
    if isinstance(parts_cost, (int, float)) and computed["labor_cost_eur"] is not None:
        computed["total_claim_cost_eur"] = round(computed["labor_cost_eur"] + float(parts_cost), 2)

    validation_summary["labor_valid"] = True
    validation_summary["cost_valid"] = True
    if labor_cost_rule and isinstance(labor_hours, (int, float)):
        if float(labor_hours) > float(labor_cost_rule.get("max_labor_hours_without_approval", 0)):
            validation_summary["labor_valid"] = False
            _handle_threshold_breach(
                attachments=attachments,
                warning_code="LABOR_THRESHOLD_EXCEEDED",
                warning_message="Labor hours exceed the allowed threshold and require human review.",
                missing_item="prior approval document",
                missing_message="Prior approval is required because labor hours exceed the allowed threshold.",
                warning_flag="LABOR_THRESHOLD_EXCEEDED",
                missing_flag="PRIOR_APPROVAL_REQUIRED",
                warn_fn=warn,
                need_fn=need,
            )

    if labor_cost_rule and isinstance(parts_cost, (int, float)):
        if float(parts_cost) > float(labor_cost_rule.get("max_parts_cost_eur_without_approval", 0)):
            validation_summary["cost_valid"] = False
            _handle_threshold_breach(
                attachments=attachments,
                warning_code="PARTS_COST_THRESHOLD_EXCEEDED",
                warning_message="Parts cost exceeds the allowed threshold and requires human review.",
                missing_item="prior approval document",
                missing_message="Prior approval is required because parts cost exceeds the allowed threshold.",
                warning_flag="PARTS_COST_THRESHOLD_EXCEEDED",
                missing_flag="COST_APPROVAL_REQUIRED",
                warn_fn=warn,
                need_fn=need,
            )
        if computed["total_claim_cost_eur"] is not None and computed["total_claim_cost_eur"] > float(labor_cost_rule.get("max_total_claim_cost_eur_without_approval", 0)):
            validation_summary["cost_valid"] = False
            _handle_threshold_breach(
                attachments=attachments,
                warning_code="TOTAL_COST_THRESHOLD_EXCEEDED",
                warning_message="Total claim cost exceeds the allowed threshold and requires human review.",
                missing_item="prior approval document",
                missing_message="Prior approval is required because total claim cost exceeds the allowed threshold.",
                warning_flag="TOTAL_COST_THRESHOLD_EXCEEDED",
                missing_flag="COST_APPROVAL_REQUIRED",
                warn_fn=warn,
                need_fn=need,
            )

    validation_summary["documents_valid"] = True
    story = extract_failure_story_sections(claim.get("failure_description"))
    if not story["is_complete"]:
        validation_summary["documents_valid"] = False
        need("failure_description", "Failure description is required.", "FAILURE_STORY_INCOMPLETE")

    if component_rule and component_rule.get("requires_diagnostic_code"):
        if not (contains_attachment(attachments, "dtc") or contains_attachment(attachments, "diagnostic")):
            validation_summary["documents_valid"] = False
            need("diagnostic trouble code report", "Diagnostic evidence is required for this repair operation.", "DIAGNOSTIC_REQUIRED")

    if component_rule and component_rule.get("requires_photo"):
        if not (contains_attachment(attachments, "photo") or contains_attachment(attachments, "image")):
            validation_summary["documents_valid"] = False
            need("photo attachment", "Photo evidence is required for this repair operation.", "PHOTO_REQUIRED")

    if component_rule and component_rule.get("requires_prior_approval"):
        if not (contains_attachment(attachments, "approval") or contains_attachment(attachments, "prior", "approval")):
            validation_summary["documents_valid"] = False
            need("prior approval document", "Prior approval is required for this repair operation.", "PRIOR_APPROVAL_MISSING")

    prior_repair_signals = _collect_prior_repair_signals(
        claim=claim,
        component_rule=component_rule,
        prior_repairs=find_prior_repairs_by_vin(claim["vin"], data),
        repair_order_date=repair_order_date,
        mileage=mileage,
    )
    duplicate_records = prior_repair_signals["duplicate_records"]
    repeat_repairs = prior_repair_signals["repeat_repairs"]
    related_repairs = prior_repair_signals["related_repairs"]
    same_part_claim_records = prior_repair_signals["same_part_claim_records"]
    same_part_claim_count = prior_repair_signals["same_part_claim_count"]
    mileage_anomaly = prior_repair_signals["mileage_anomaly"]

    refs["prior_repair_history_ids"] = sorted(
        {
            record.get("history_id")
            for record in duplicate_records + repeat_repairs + related_repairs + same_part_claim_records
            if record.get("history_id")
        }
    )

    validation_summary["duplicate_risk"] = bool(duplicate_records)
    validation_summary["prior_repair_risk"] = bool(repeat_repairs or same_part_claim_records)
    validation_summary["mileage_anomaly"] = mileage_anomaly
    if duplicate_records:
        warn("POSSIBLE_DUPLICATE", "A duplicate candidate was found for the same VIN, repair code, and causal part within 30 days.", "POSSIBLE_DUPLICATE")
    if repeat_repairs:
        warn("REPEAT_REPAIR_CANDIDATE", "A repeat repair candidate was found for the same causal part within 12 months.", "REPEAT_REPAIR_CANDIDATE")
    if same_part_claim_count >= 3:
        fail(
            "SAME_PART_CLAIM_LIMIT_EXCEEDED",
            f"The same causal part has already been claimed {same_part_claim_count} times for this VIN; a fourth claim is not allowed.",
            "SAME_PART_CLAIM_LIMIT_EXCEEDED",
        )
    if related_repairs and not duplicate_records and not repeat_repairs:
        warn("RELATED_PRIOR_REPAIR", "A related prior repair exists for the same VIN and component group.", "RELATED_PRIOR_REPAIR")
    if mileage_anomaly:
        fail("MILEAGE_ANOMALY", "Current mileage is lower than a prior repair mileage for the same VIN.", "MILEAGE_ANOMALY")

    service_history_signals = _collect_service_history_signals(
        vin=claim["vin"],
        service_history=find_service_history_by_vin(claim["vin"], data),
        repair_order_date=repair_order_date,
        mileage=mileage,
    )
    refs["service_history_ids"] = [
        record.get("service_id")
        for record in service_history_signals["records"]
        if record.get("service_id")
    ]
    validation_summary["service_history_complete"] = service_history_signals["service_history_complete"]
    validation_summary["service_gap_risk"] = service_history_signals["service_gap_detected"]
    validation_summary["maintenance_compliance"] = not bool(service_history_signals["non_compliant_records"])

    if not service_history_signals["service_history_complete"]:
        warn("LIMITED_SERVICE_HISTORY", "Service history is limited for this VIN.", "LIMITED_SERVICE_HISTORY")
    if not service_history_signals["coolant_records"]:
        warn("NO_COOLANT_SERVICE_HISTORY", "No coolant-related service record was found before the claim date.", "NO_COOLANT_SERVICE_HISTORY")
    if service_history_signals["service_gap_detected"]:
        warn("SERVICE_GAP_OVER_12_MONTHS", "A service gap greater than 12 months was found in service history.", "SERVICE_GAP_OVER_12_MONTHS")
    if service_history_signals["oem_gap_records"]:
        warn("NON_AUTHORIZED_SERVICE_HISTORY", "One or more non-authorized service records were found for this VIN.", "NON_AUTHORIZED_SERVICE_HISTORY")
    if service_history_signals["open_records"]:
        warn("OPEN_SERVICE_RECORD_PRESENT", "An open service record exists for this VIN.", "OPEN_SERVICE_RECORD_PRESENT")
    if service_history_signals["cancelled_records"]:
        warn("CANCELLED_SERVICE_RECORD_PRESENT", "A cancelled service record exists for this VIN.", "CANCELLED_SERVICE_RECORD_PRESENT")
    if service_history_signals["mileage_anomaly"]:
        fail("SERVICE_HISTORY_MILEAGE_ANOMALY", "Service history contains a mileage anomaly for this VIN.", "SERVICE_HISTORY_MILEAGE_ANOMALY")

    lack_of_maintenance_records = [
        record
        for record in service_history_signals["non_compliant_records"]
        if "lack of maintenance" in str(record.get("technician_notes", "")).lower()
    ]
    contamination_records = [
        record
        for record in service_history_signals["records"]
        if "contaminated coolant" in str(record.get("technician_notes", "")).lower()
        or "coolant sample showed contamination" in str(record.get("technician_notes", "")).lower()
    ]
    if lack_of_maintenance_records:
        fail("LACK_OF_MAINTENANCE_HISTORY", "Service history indicates lack of maintenance.", "LACK_OF_MAINTENANCE_HISTORY")
    if contamination_records:
        warn("COOLANT_CONTAMINATION_HISTORY", "Service history includes coolant contamination findings.", "COOLANT_CONTAMINATION_HISTORY")

    exclusion_keyword_analysis = scan_exclusion_keywords(claim.get("failure_description"))
    validation_summary["exclusion_risk"] = bool(exclusion_keyword_analysis["keywords_found"])
    if exclusion_keyword_analysis["keywords_found"]:
        warn("EXCLUSION_KEYWORDS_FOUND", f"Exclusion keywords found: {', '.join(exclusion_keyword_analysis['keywords_found'])}.", "EXCLUSION_KEYWORDS_FOUND")

    overall_rule_status = "PASS"
    recommended_disposition = "CONTINUE"
    rule_summary = "All business-rule validations passed."

    if failed_checks:
        overall_rule_status = "BLOCKED"
        recommended_disposition = "REJECT"
        rule_summary = "Business-rule validation found blocking failures."
    elif missing_info:
        overall_rule_status = "PASS_WITH_WARNINGS"
        recommended_disposition = "MORE_INFO"
        rule_summary = "Business-rule validation requires additional supporting information."
    elif any(item["code"] in {"POSSIBLE_DUPLICATE", "REPEAT_REPAIR_CANDIDATE", "REPAIR_CODE_PART_MISMATCH", "EXCLUSION_KEYWORDS_FOUND"} for item in warnings):
        overall_rule_status = "PASS_WITH_WARNINGS"
        recommended_disposition = "REFER_TO_HUMAN"
        rule_summary = "Business-rule validation identified items requiring human review."
    elif warnings:
        overall_rule_status = "PASS_WITH_WARNINGS"
        recommended_disposition = "CONTINUE"
        rule_summary = "Business-rule validation passed with non-blocking warnings."

    return _make_compact_result(
        claim,
        gateway_status="CONTINUE",
        overall_rule_status=overall_rule_status,
        recommended_disposition=recommended_disposition,
        rule_confidence=calculate_rule_confidence(failed_checks, warnings),
        rule_summary=rule_summary,
        refs=refs,
        computed=computed,
        validation_summary=validation_summary,
        failed_checks=failed_checks,
        warnings=warnings,
        missing_info=missing_info,
        flags=flags,
        goodwill_precheck=gateway_result.get("goodwill_precheck"),
    )


def run_rule_engine(claim: dict[str, Any]) -> dict[str, Any]:
    claim_payload = dict(claim)
    claim_payload.setdefault("claim_id", generate_claim_id())

    try:
        data = _load_all_data()
    except (FileNotFoundError, ValueError) as exc:
        return _make_compact_result(
            claim_payload,
            gateway_status="TERMINAL",
            overall_rule_status="BLOCKED",
            recommended_disposition="REFER_TO_HUMAN",
            rule_confidence=0.25,
            rule_summary=f"Rule engine configuration error: {exc}",
            failed_checks=[{"code": "ENGINE_DATA_ERROR", "message": str(exc)}],
            flags=["ENGINE_DATA_ERROR"],
        )

    gateway_result = run_gateway_validation(claim_payload, data)
    if gateway_result.get("gateway_status") == "TERMINAL":
        return gateway_result
    return run_full_claim_validation(claim_payload, gateway_result, data)


def _load_claim_from_cli() -> dict[str, Any]:
    if len(sys.argv) > 1:
        raw = Path(sys.argv[1]).read_text()
    else:
        raw = sys.stdin.read()
    return json.loads(raw)


if __name__ == "__main__":
    print(json.dumps(run_rule_engine(_load_claim_from_cli()), indent=2))
