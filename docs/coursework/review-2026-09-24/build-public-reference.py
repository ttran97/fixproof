"""Build the sanitized data file for the FixProof public reference site.

This exporter deliberately selects a small public schema. It does not copy raw
reports, model response identifiers, local paths, hashes, or review packets.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / "fixproof-public" / "data" / "public-evidence.json"
EXTENSION_RUN_ID = "20260930T180925912688Z-path-s06-v1"
EXTENSION_SUMMARY = (
    ROOT
    / "data"
    / "extensions"
    / "path-s06-v1"
    / "runs"
    / EXTENSION_RUN_ID
    / "summary.json"
)
EXTENSION_REVIEWS = ROOT / "data" / "extensions" / "path-s06-v1" / "human-reviews"

CASE_ORDER = {"xss": 0, "sqli": 1, "path-traversal": 2}
CASE_LABELS = {
    "xss": "Reflected XSS",
    "sqli": "SQL injection",
    "path-traversal": "Path traversal",
}
SHORT_LABELS = {
    "xss": "XSS",
    "sqli": "SQLi",
    "path-traversal": "Traversal",
}
CATEGORY_LABELS = {
    "security": "Security",
    "behavioral_parity": "Behavioral parity",
    "robustness_contract": "Robustness",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def checked_binding(binding: dict[str, Any]) -> dict[str, Any]:
    path = (ROOT / str(binding["path"])).resolve()
    if not path.is_relative_to(ROOT.resolve()) or not path.is_file():
        raise ValueError(f"Bound public evidence is missing: {binding['path']}")
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != binding.get("sha256"):
        raise ValueError(f"Bound public evidence changed: {binding['path']}")
    return load_json(path)


def public_review(record: dict[str, Any] | None) -> dict[str, str] | None:
    if not record or not record.get("verdict"):
        return None
    return {
        "verdict": str(record["verdict"]),
        "reviewed_on": str(record.get("reviewed_at", ""))[:10],
        "rationale": str(record.get("rationale", "")).strip(),
    }


def patch_excerpt(patch: str) -> str:
    changed = [
        line
        for line in patch.splitlines()
        if line.startswith(("+", "-"))
        and not line.startswith(("+++", "---"))
    ]
    if len(changed) > 28:
        changed = [*changed[:28], "... excerpt shortened for the public view ..."]
    return "\n".join(changed)


def category_counts(summary: dict[str, Any], category: str) -> dict[str, int]:
    raw = summary.get("by_category", {}).get(category, {})
    return {
        "total": int(raw.get("total", 0)),
        "pass": int(raw.get("pass", 0)),
        "fail": int(raw.get("fail", 0)),
        "inconclusive": int(raw.get("inconclusive", 0)),
    }


def public_nonpassing(result: dict[str, Any]) -> list[dict[str, str]]:
    public: list[dict[str, str]] = []
    for case in result.get("cases", []):
        evaluation = case.get("candidate_expectation_evaluation", {})
        status = str(evaluation.get("status", "")).lower()
        if status == "pass":
            continue
        category = str(case.get("category", ""))
        public.append(
            {
                "test_id": str(case.get("test_id", "")),
                "category": CATEGORY_LABELS.get(category, category),
                "status": status or "unknown",
                "reason": str(evaluation.get("reason", "")).strip(),
            }
        )
    return public


def main() -> None:
    primary = load_json(ROOT / "data" / "evaluation" / "primary-report.json")
    supplemental = load_json(
        ROOT / "data" / "supplemental" / "v1" / "supplemental-report.json"
    )
    extension_summary = load_json(EXTENSION_SUMMARY)
    if (
        extension_summary.get("status") != "complete"
        or extension_summary.get("candidate_counts")
        != {"pass": 0, "fail": 5, "inconclusive": 0}
        or extension_summary.get("protected_data_unchanged") is not True
    ):
        raise ValueError("PATH-S06 extension summary is incomplete or unexpected.")

    extension_candidates: dict[str, dict[str, Any]] = {}
    for row in extension_summary["candidate_results"]:
        result = checked_binding(
            {"path": row["result"], "sha256": row["sha256"]}
        )
        evaluation = result["evaluation"]
        response = result["response"]
        if (
            evaluation.get("status") != "fail"
            or evaluation.get("marker_disclosed") is not True
            or response.get("status_code") != 200
        ):
            raise ValueError(f"Unexpected PATH-S06 result: {row['target_id']}")
        extension_candidates[str(row["target_id"])] = result

    extension_reviews: dict[str, dict[str, Any]] = {}
    for result_path in sorted(EXTENSION_REVIEWS.glob("*/result.json")):
        result = load_json(result_path)
        if result.get("status") != "completed":
            raise ValueError(f"Incomplete PATH-S06 human record: {result_path}")
        checked_binding(result["approval"])
        packet = checked_binding(result["packet"])
        checked_binding(result["extension_candidate_result"])
        if result["extension_candidate_result"] != packet["extension_candidate_result"]:
            raise ValueError(f"PATH-S06 review binds another result: {result_path}")
        extension_reviews[str(result["trial_id"])] = result
    if len(extension_candidates) != 5 or len(extension_reviews) != 5:
        raise ValueError("Expected five PATH-S06 results and five human records.")

    followups: dict[str, dict[str, Any]] = {}
    followup_root = ROOT / "data" / "supplemental" / "v1" / "follow-up-reviews"
    for result_path in sorted(followup_root.glob("*/result.json")):
        result = load_json(result_path)
        followups[str(result["trial_id"])] = result

    supplemental_candidates: dict[tuple[str, int], dict[str, Any]] = {}
    for cwe in supplemental["cwes"]:
        case_id = str(cwe["cwe_case"])
        for candidate in cwe["candidates"]:
            supplemental_candidates[(case_id, int(candidate["attempt"]))] = candidate

    candidates: list[dict[str, Any]] = []
    for row in primary["experiment_matrix"]:
        case_id = str(row["case_id"])
        attempt = int(row["attempt"])
        trial_id = str(row["trial_id"])
        supplemental_entry = supplemental_candidates[(case_id, attempt)]
        supplemental_result = load_json(ROOT / supplemental_entry["path"])
        summary = supplemental_entry["summary"]
        security = row["evidence"]["security"]
        functional = row["evidence"]["functional"]

        candidates.append(
            {
                "id": f"{SHORT_LABELS[case_id]} {attempt:02d}",
                "trial_id": trial_id,
                "case_id": case_id,
                "case": CASE_LABELS[case_id],
                "cwe": str(row["cwe"]),
                "attempt": attempt,
                "primary": {
                    "target_sast": str(row["evidence"]["target_sast"]),
                    "security": {
                        "passed": int(security["passed"]),
                        "total": int(security["total"]),
                    },
                    "functional": {
                        "passed": int(functional["passed"]),
                        "total": int(functional["total"]),
                    },
                    "automated_decision": str(row["decision"]),
                    "original_human": public_review(row.get("adjudication")),
                },
                "supplemental": {
                    "registered": int(summary["registered"]),
                    "pass": int(summary["pass"]),
                    "fail": int(summary["fail"]),
                    "inconclusive": int(summary["inconclusive"]),
                    "security": category_counts(summary, "security"),
                    "parity": category_counts(summary, "behavioral_parity"),
                    "robustness": category_counts(summary, "robustness_contract"),
                    "nonpassing": public_nonpassing(supplemental_result),
                    "later_human": public_review(followups.get(trial_id)),
                },
                "path_s06_extension": (
                    {
                        "status": str(
                            extension_candidates[trial_id]["evaluation"]["status"]
                        ),
                        "status_code": int(
                            extension_candidates[trial_id]["response"]["status_code"]
                        ),
                        "marker_disclosed": bool(
                            extension_candidates[trial_id]["evaluation"][
                                "marker_disclosed"
                            ]
                        ),
                        "human": public_review(extension_reviews[trial_id]),
                        "relationship_to_prior_follow_up": str(
                            extension_reviews[trial_id][
                                "relationship_to_prior_follow_up"
                            ]
                        ),
                        "manual_reproduction": bool(
                            extension_reviews[trial_id]["manual_reproduction"]
                        ),
                    }
                    if trial_id in extension_candidates
                    else None
                ),
                "patch_excerpt": patch_excerpt(row["review_material"]["patch"]),
            }
        )

    candidates.sort(key=lambda item: (CASE_ORDER[item["case_id"]], item["attempt"]))

    primary_metrics = primary["metrics"]
    public = {
        "schema_version": "1.1-public",
        "project": "FixProof",
        "generated_on": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "evidence_cutoff": supplemental["evidence_cutoff"],
        "scope": {
            "description": (
                "Three controlled Express fixtures and five initial repair attempts "
                "per fixture. Results are descriptive and do not estimate production "
                "repair reliability."
            ),
            "generator": "gpt-5.2 with one fixed prompt condition and no model tools",
            "authority_boundary": (
                "The model proposed code. Separate validators measured it. Human "
                "decisions remained separate from automated policy states."
            ),
            "recording_note": (
                "This site presents saved evidence only. It does not call a model, "
                "scan code, run attacks, approve a patch, or deploy repaired software."
            ),
        },
        "primary_summary": {
            "attempts": int(primary["attempt_count"]),
            "target_sast_resolved": int(primary_metrics["sast_remediation_success"]["count"]),
            "security_passed_candidates": int(primary_metrics["targeted_security_pass"]["count"]),
            "functional_passed_candidates": int(primary_metrics["functional_preservation"]["count"]),
            "sast_runtime_disagreements": int(primary_metrics["sast_runtime_disagreement"]["count"]),
            "original_human_reviews": int(primary["adjudication_summary"]["completed"]),
            "unique_candidate_sources": {
                key: int(value) for key, value in primary["unique_candidate_sources"].items()
            },
        },
        "supplemental_summary": {
            "case_definitions": int(supplemental["definition"]["cases"]["test_count"]),
            "saved_candidates": int(supplemental["saved_candidate_count"]),
            "candidate_case_observations": supplemental["candidate_case_observations"],
            "by_category": supplemental["candidate_observations_by_category"],
            "later_human_records": len(followups),
        },
        "path_s06_extension_summary": {
            "protocol_id": "path-s06-extension-v1",
            "run_id": EXTENSION_RUN_ID,
            "candidate_observations": extension_summary["candidate_counts"],
            "human_qualifications": len(extension_reviews),
            "manual_reproductions": sum(
                bool(record["manual_reproduction"])
                for record in extension_reviews.values()
            ),
            "recording_note": (
                "This separately versioned extension does not change the five "
                "inconclusive PATH-S06 observations in supplemental-v1."
            ),
        },
        "limitations": [
            *primary["limitations"],
            "The five PATH-S06 observations remain inconclusive in supplemental-v1; a separate WSL2 extension later recorded five security failures.",
            "The SQL injection target comparison uses a separately labeled controlled Semgrep rule.",
            "Supplemental security, behavioral-parity, and robustness counts answer different questions and should not be pooled into one security rate.",
        ],
        "candidates": candidates,
    }

    assert len(candidates) == 15
    assert len(followups) == 14
    assert sum(1 for item in candidates if item["primary"]["original_human"]) == 10
    assert sum(1 for item in candidates if item["supplemental"]["later_human"]) == 14
    assert sum(1 for item in candidates if item["path_s06_extension"]) == 5
    assert sum(
        1
        for item in candidates
        if item["path_s06_extension"]
        and item["path_s06_extension"]["human"]
    ) == 5
    assert public["supplemental_summary"]["candidate_case_observations"] == {
        "total": 140,
        "pass": 120,
        "fail": 15,
        "inconclusive": 5,
    }

    serialized = json.dumps(public, ensure_ascii=False, indent=2) + "\n"
    forbidden = {
        "local Windows paths": "C:\\\\Users\\\\",
        "OpenAI response identifiers": "resp_",
        "API key variable": "OPENAI_API_KEY",
        "hash fields": '"sha256"',
    }
    for label, marker in forbidden.items():
        if marker in serialized:
            raise ValueError(f"Public export contains forbidden {label}: {marker}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(serialized, encoding="utf-8")
    print(f"Created {OUTPUT}")
    print(
        f"Candidates: {len(candidates)}; supplemental human records: "
        f"{len(followups)}; PATH-S06 qualifications: {len(extension_reviews)}"
    )


if __name__ == "__main__":
    main()
