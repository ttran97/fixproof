from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


POLICY_VERSION = "0.2-evidence-aware"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def validate_canonical_ids(
    preliminary: dict[str, Any],
    security: dict[str, Any],
    functional: dict[str, Any],
) -> str:

    ids = {
        preliminary[
            "validation"
        ]["canonical_id"],

        security[
            "security_validation"
        ]["canonical_id"],

        functional[
            "functional_validation"
        ]["canonical_id"],
    }

    if len(ids) != 1:
        raise ValueError(
            "Validation artifacts contain "
            f"different canonical IDs: {ids}"
        )

    return ids.pop()


def classify_outcome(
    syntax_status: str,
    target_sast_status: str,
    new_findings: int,
    security_status: str,
    functional_status: str,
) -> str:

    if syntax_status != "pass":
        return "syntax_failure"

    if new_findings > 0:
        return "security_regression"

    # SAST disappeared, but downstream validation failed.
    if (
        target_sast_status == "resolved"
        and (
            security_status != "pass"
            or functional_status != "pass"
        )
    ):
        return "sast_false_success"

    if (
        target_sast_status == "persistent"
        and functional_status == "fail"
    ):
        return (
            "persistent_target_with_"
            "functional_regression"
        )

    if (
        target_sast_status == "persistent"
        and security_status == "fail"
    ):
        return (
            "persistent_target_with_"
            "security_failure"
        )

    # Important FixProof evidence-conflict state.
    if (
        target_sast_status == "persistent"
        and security_status == "pass"
        and functional_status == "pass"
        and new_findings == 0
    ):
        return "sast_runtime_disagreement"

    if security_status == "fail":
        return "security_validation_failure"

    if security_status == "inconclusive":
        return "security_validation_inconclusive"

    if functional_status == "fail":
        return "functional_regression"

    if (
        target_sast_status == "resolved"
        and security_status == "pass"
        and functional_status == "pass"
        and new_findings == 0
    ):
        return "validated_candidate"

    return "unclassified_validation_state"


def determine_disposition(
    syntax_status: str,
    target_sast_status: str,
    new_findings: int,
    security_status: str,
    functional_status: str,
) -> dict[str, Any]:
    """
    FixProof evidence-aware policy.

    REJECT:
        A deterministic validation layer demonstrated
        a concrete failure.

    READY_FOR_HUMAN_REVIEW:
        SAST resolved, runtime security passed,
        functionality passed, and no new findings.

    NEEDS_HUMAN_ADJUDICATION:
        SAST remains persistent, but runtime security
        and functionality both pass and there are no
        new findings.

    The AI never approves its own patch.
    """

    # -------------------------------------------------
    # Concrete failure states
    # -------------------------------------------------

    reason_codes = []

    if syntax_status != "pass":
        reason_codes.append(
            "SYNTAX_VALIDATION_FAILED"
        )

    if new_findings > 0:
        reason_codes.append(
            "NEW_SECURITY_FINDINGS"
        )

    if security_status == "fail":
        reason_codes.append(
            "TARGET_SECURITY_TEST_FAILED"
        )

    elif security_status == "inconclusive":
        reason_codes.append(
            "TARGET_SECURITY_TEST_INCONCLUSIVE"
        )

    if functional_status != "pass":
        reason_codes.append(
            "FUNCTIONAL_REGRESSION"
        )

    concrete_failure = (
        syntax_status != "pass"
        or new_findings > 0
        or security_status != "pass"
        or functional_status != "pass"
    )

    if concrete_failure:

        if (
            target_sast_status
            == "persistent"
        ):
            reason_codes.append(
                "TARGET_SAST_FINDING_PERSISTENT"
            )

        return {
            "disposition": "REJECT",

            "eligible_for_human_approval": False,

            "retry_allowed": True,

            "recommended_action": (
                "generate_new_candidate"
            ),

            "reason_codes": (
                reason_codes
            ),
        }

    # -------------------------------------------------
    # All downstream validation passed and SAST agrees
    # -------------------------------------------------

    if target_sast_status == "resolved":

        return {
            "disposition": (
                "READY_FOR_HUMAN_REVIEW"
            ),

            "eligible_for_human_approval": True,

            "retry_allowed": False,

            "recommended_action": (
                "present_candidate_for_"
                "human_review"
            ),

            "reason_codes": [],
        }

    # -------------------------------------------------
    # SAST/runtime disagreement
    # -------------------------------------------------

    if target_sast_status == "persistent":

        return {
            "disposition": (
                "NEEDS_HUMAN_ADJUDICATION"
            ),

            "eligible_for_human_approval": False,

            "retry_allowed": False,

            "recommended_action": (
                "human_adjudication"
            ),

            "reason_codes": [
                (
                    "TARGET_SAST_FINDING_"
                    "PERSISTENT"
                ),
                (
                    "SAST_RUNTIME_EVIDENCE_"
                    "CONFLICT"
                ),
            ],
        }

    # -------------------------------------------------
    # Unknown/unexpected state
    # -------------------------------------------------

    return {
        "disposition": "REJECT",

        "eligible_for_human_approval": False,

        "retry_allowed": False,

        "recommended_action": (
            "inspect_validation_state"
        ),

        "reason_codes": [
            "UNCLASSIFIED_VALIDATION_STATE"
        ],
    }


def detect_evidence_conflict(
    target_sast_status: str,
    security_status: str,
    functional_status: str,
    new_findings: int,
) -> dict[str, Any]:

    conflict = (
        target_sast_status == "persistent"
        and security_status == "pass"
        and functional_status == "pass"
        and new_findings == 0
    )

    if conflict:
        description = (
            "The target SAST finding remained "
            "persistent while targeted runtime "
            "security validation and functional "
            "validation both passed with no new "
            "SAST findings."
        )
    else:
        description = None

    return {
        "detected": conflict,
        "description": description,
    }


def determine_human_review_state(
    disposition: str,
) -> dict[str, Any]:

    if disposition == (
        "READY_FOR_HUMAN_REVIEW"
    ):
        return {
            "status": "ready",
            "purpose": (
                "final_candidate_approval"
            ),
        }

    if disposition == (
        "NEEDS_HUMAN_ADJUDICATION"
    ):
        return {
            "status": (
                "adjudication_required"
            ),
            "purpose": (
                "resolve_conflicting_"
                "validation_evidence"
            ),
        }

    return {
        "status": "not_ready",
        "purpose": None,
    }


def run_decision_engine(
    preliminary_file: Path,
    security_file: Path,
    functional_file: Path,
    output_file: Path,
) -> dict[str, Any]:

    print("=" * 60)
    print(
        "FixProof Remediation Decision Engine"
    )
    print("=" * 60)

    preliminary = load_json(
        preliminary_file
    )

    security = load_json(
        security_file
    )

    functional = load_json(
        functional_file
    )

    canonical_id = validate_canonical_ids(
        preliminary=preliminary,
        security=security,
        functional=functional,
    )

    preliminary_validation = preliminary[
        "validation"
    ]

    security_validation = security[
        "security_validation"
    ]

    functional_validation = functional[
        "functional_validation"
    ]

    syntax_status = (
        preliminary_validation[
            "syntax"
        ]["status"]
    )

    target_sast_status = (
        preliminary_validation[
            "comparison"
        ]["target"]["status"]
    )

    new_findings = (
        preliminary_validation[
            "comparison"
        ]["summary"]["new"]
    )

    security_status = (
        security_validation[
            "status"
        ]
    )

    functional_status = (
        functional_validation[
            "status"
        ]
    )

    functional_passed = (
        functional_validation[
            "summary"
        ]["passed"]
    )

    functional_failed = (
        functional_validation[
            "summary"
        ]["failed"]
    )

    classification = classify_outcome(
        syntax_status=syntax_status,
        target_sast_status=(
            target_sast_status
        ),
        new_findings=new_findings,
        security_status=(
            security_status
        ),
        functional_status=(
            functional_status
        ),
    )

    disposition = determine_disposition(
        syntax_status=syntax_status,
        target_sast_status=(
            target_sast_status
        ),
        new_findings=new_findings,
        security_status=(
            security_status
        ),
        functional_status=(
            functional_status
        ),
    )

    evidence_conflict = (
        detect_evidence_conflict(
            target_sast_status=(
                target_sast_status
            ),
            security_status=(
                security_status
            ),
            functional_status=(
                functional_status
            ),
            new_findings=(
                new_findings
            ),
        )
    )

    sast_remediation_success = (
        target_sast_status == "resolved"
    )

    security_validation_pass = (
        security_status == "pass"
    )

    functional_preservation = (
        functional_status == "pass"
    )

    security_regression = (
        new_findings > 0
    )

    false_success = (
        sast_remediation_success
        and (
            not security_validation_pass
            or not functional_preservation
            or security_regression
        )
    )

    human_review = (
        determine_human_review_state(
            disposition[
                "disposition"
            ]
        )
    )

    result = {
        "schema_version": "0.2",
        "project": "FixProof",

        "decision": {
            "canonical_id": (
                canonical_id
            ),

            "policy_version": (
                POLICY_VERSION
            ),

            "classification": (
                classification
            ),

            "disposition": (
                disposition[
                    "disposition"
                ]
            ),

            "eligible_for_human_approval": (
                disposition[
                    "eligible_for_human_approval"
                ]
            ),

            "retry_allowed": (
                disposition[
                    "retry_allowed"
                ]
            ),

            "recommended_action": (
                disposition[
                    "recommended_action"
                ]
            ),

            "reason_codes": (
                disposition[
                    "reason_codes"
                ]
            ),

            "evidence": {
                "syntax": (
                    syntax_status
                ),

                "target_sast": (
                    target_sast_status
                ),

                "new_sast_findings": (
                    new_findings
                ),

                "security_validation": (
                    security_status
                ),

                "functional_validation": (
                    functional_status
                ),

                "functional_tests": {
                    "passed": (
                        functional_passed
                    ),

                    "failed": (
                        functional_failed
                    ),
                },
            },

            "evidence_conflict": (
                evidence_conflict
            ),

            "evaluation_labels": {
                "sast_remediation_success": (
                    sast_remediation_success
                ),

                "security_validation_pass": (
                    security_validation_pass
                ),

                "functional_preservation": (
                    functional_preservation
                ),

                "security_regression": (
                    security_regression
                ),

                "false_success": (
                    false_success
                ),
            },

            "human_review": {
                "status": (
                    human_review[
                        "status"
                    ]
                ),

                "purpose": (
                    human_review[
                        "purpose"
                    ]
                ),

                "note": (
                    "FixProof never automatically "
                    "approves an AI-generated "
                    "remediation. Human review "
                    "remains required."
                ),
            },

            "input_artifacts": {
                "preliminary": str(
                    preliminary_file
                ),

                "security": str(
                    security_file
                ),

                "functional": str(
                    functional_file
                ),
            },
        },
    }

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file.write_text(
        json.dumps(
            result,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        f"Canonical finding: "
        f"{canonical_id}"
    )

    print()
    print("Validation Evidence")
    print("-" * 60)

    print(
        f"Syntax: "
        f"{syntax_status}"
    )

    print(
        f"Target SAST: "
        f"{target_sast_status}"
    )

    print(
        f"New SAST findings: "
        f"{new_findings}"
    )

    print(
        f"Security validation: "
        f"{security_status}"
    )

    print(
        f"Functional validation: "
        f"{functional_status}"
    )

    print()

    print(
        f"Classification: "
        f"{classification}"
    )

    print(
        f"Evidence conflict: "
        f"{evidence_conflict['detected']}"
    )

    print(
        f"False success: "
        f"{false_success}"
    )

    print()

    print("=" * 60)

    print(
        "FixProof Decision: "
        f"{disposition['disposition']}"
    )

    print("=" * 60)

    if disposition[
        "reason_codes"
    ]:

        print("Reasons:")

        for reason in disposition[
            "reason_codes"
        ]:

            print(
                f"- {reason}"
            )

    print()

    print(
        f"Retry allowed: "
        f"{disposition['retry_allowed']}"
    )

    print(
        f"Recommended action: "
        f"{disposition['recommended_action']}"
    )

    print(
        f"Human review state: "
        f"{human_review['status']}"
    )

    print(
        f"Report: {output_file}"
    )

    return result


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Combine independent FixProof "
            "validation evidence and determine "
            "the remediation disposition."
        )
    )

    parser.add_argument(
        "--preliminary",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--security",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--functional",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--output",
        required=True,
        type=Path,
    )

    args = parser.parse_args()

    run_decision_engine(
        preliminary_file=(
            args.preliminary.resolve()
        ),

        security_file=(
            args.security.resolve()
        ),

        functional_file=(
            args.functional.resolve()
        ),

        output_file=(
            args.output.resolve()
        ),
    )


if __name__ == "__main__":
    main()