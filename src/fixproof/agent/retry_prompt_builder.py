from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


RETRY_SYSTEM_INSTRUCTIONS = """
You are the remediation component of FixProof, a security patch
generation system.

A previous candidate remediation failed independent validation.

Your task is to generate a NEW candidate remediation for the same
canonical security finding using the supplied source context and
validation evidence.

Requirements:

1. Address exactly the supplied canonical security finding.
2. Preserve the application's intended behavior.
3. Correct the problems demonstrated by the previous validation results.
4. Do not repeat a candidate known to have failed validation.
5. Do not disable, suppress, ignore, or bypass the security scanner.
6. Do not remove application functionality merely to eliminate a finding.
7. Do not make unrelated source-code changes.
8. Do not assume that either static analysis or runtime testing alone is
   sufficient evidence.
9. Prefer a minimal source-code change.
10. Do not claim that the new remediation is successful. FixProof will
    independently validate it.

Return JSON only.

Required JSON structure:

{
  "canonical_id": "...",
  "analysis": "...",
  "remediation_strategy": "...",
  "patched_code": "...",
  "assumptions": [],
  "needs_additional_context": false
}
""".strip()


def load_json(
    path: Path,
) -> dict[str, Any]:
    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def find_original_prompt(
    prompt_data: dict[str, Any],
    canonical_id: str,
) -> dict[str, Any]:

    for prompt in prompt_data.get(
        "prompts",
        [],
    ):
        if (
            prompt.get("canonical_id")
            == canonical_id
        ):
            return prompt

    raise ValueError(
        f"Original prompt not found "
        f"for {canonical_id}"
    )


def build_retry_prompt(
    canonical_id: str,
    original_prompt: dict[str, Any],
    previous_remediation: dict[str, Any],
    preliminary: dict[str, Any],
    security: dict[str, Any],
    functional: dict[str, Any],
    decision: dict[str, Any],
) -> str:

    remediation = previous_remediation[
        "remediation"
    ]

    preliminary_validation = preliminary[
        "validation"
    ]

    security_validation = security[
        "security_validation"
    ]

    functional_validation = functional[
        "functional_validation"
    ]

    decision_data = decision[
        "decision"
    ]

    failed_functional_tests = []

    for test in functional_validation.get(
        "tests",
        [],
    ):
        if (
            test.get(
                "evaluation",
                {},
            ).get("status")
            == "fail"
        ):
            failed_functional_tests.append(
                {
                    "test": test.get(
                        "test"
                    ),
                    "input": test.get(
                        "input"
                    ),
                    "expected": test.get(
                        "evaluation",
                        {},
                    ).get(
                        "expected_value"
                    ),
                    "actual": test.get(
                        "evaluation",
                        {},
                    ).get(
                        "decoded_value"
                    ),
                }
            )

    functional_failure_text = (
        json.dumps(
            failed_functional_tests,
            indent=2,
        )
        if failed_functional_tests
        else "None"
    )

    reason_codes = (
        decision_data.get(
            "reason_codes",
            [],
        )
    )

    return f"""
FIXPROOF REMEDIATION RETRY

Canonical Finding ID:
{canonical_id}

This is remediation attempt 2.

The previous candidate was independently validated and REJECTED.

============================================================
ORIGINAL REMEDIATION TASK
============================================================

{original_prompt["user_prompt"]}

============================================================
PREVIOUS CANDIDATE
============================================================

Previous analysis:
{remediation.get("analysis")}

Previous remediation strategy:
{remediation.get("remediation_strategy")}

Previous patched code:
------------------------------
{remediation.get("patched_code")}
------------------------------

============================================================
INDEPENDENT VALIDATION EVIDENCE
============================================================

Syntax validation:
{preliminary_validation["syntax"]["status"]}

Target SAST status:
{preliminary_validation["comparison"]["target"]["status"]}

New SAST findings:
{preliminary_validation["comparison"]["summary"]["new"]}

Targeted security validation:
{security_validation["status"]}

Functional validation:
{functional_validation["status"]}

Functional tests passed:
{functional_validation["summary"]["passed"]}

Functional tests failed:
{functional_validation["summary"]["failed"]}

Failed functional test evidence:
{functional_failure_text}

Decision-engine classification:
{decision_data.get("classification")}

Decision:
{decision_data.get("disposition")}

Reason codes:
{json.dumps(reason_codes)}

Evidence conflict:
{json.dumps(
    decision_data.get(
        "evidence_conflict",
        {},
    ),
    indent=2,
)}

============================================================
RETRY REQUIREMENTS
============================================================

Generate a different candidate remediation.

The new candidate must:

- address the original canonical security finding;
- avoid the functional corruption demonstrated by the failed tests;
- preserve ordinary and special-character user input semantics;
- avoid new security weaknesses;
- avoid scanner suppression or bypasses;
- remain minimal and scoped to the supplied source context.

Do not simply return the previous candidate again.

The patched_code field must contain the complete replacement for the
original source context and must not contain source-line prefixes or
">>" markers.

Do not decide whether your new remediation succeeds. FixProof will run
syntax validation, SAST rescanning, targeted security testing, and
functional regression testing independently.
""".strip()


def build_retry_prompt_file(
    original_prompt_file: Path,
    remediation_file: Path,
    preliminary_file: Path,
    security_file: Path,
    functional_file: Path,
    decision_file: Path,
    canonical_id: str,
    output_file: Path,
) -> dict[str, Any]:

    original_prompts = load_json(
        original_prompt_file
    )

    previous_remediation = load_json(
        remediation_file
    )

    preliminary = load_json(
        preliminary_file
    )

    security = load_json(
        security_file
    )

    functional = load_json(
        functional_file
    )

    decision = load_json(
        decision_file
    )

    original_prompt = (
        find_original_prompt(
            prompt_data=original_prompts,
            canonical_id=canonical_id,
        )
    )

    # Ensure every artifact belongs to the same finding.
    artifact_ids = {
        canonical_id,

        previous_remediation[
            "remediation"
        ]["canonical_id"],

        preliminary[
            "validation"
        ]["canonical_id"],

        security[
            "security_validation"
        ]["canonical_id"],

        functional[
            "functional_validation"
        ]["canonical_id"],

        decision[
            "decision"
        ]["canonical_id"],
    }

    if len(artifact_ids) != 1:
        raise ValueError(
            "Retry artifacts do not all "
            f"reference the same finding: "
            f"{artifact_ids}"
        )

    retry_prompt = build_retry_prompt(
        canonical_id=canonical_id,
        original_prompt=original_prompt,
        previous_remediation=(
            previous_remediation
        ),
        preliminary=preliminary,
        security=security,
        functional=functional,
        decision=decision,
    )

    result = {
        "schema_version": "0.1",
        "project": "FixProof",

        "retry": {
            "attempt": 2,
            "canonical_id": canonical_id,
            "previous_disposition": (
                decision[
                    "decision"
                ]["disposition"]
            ),
        },

        # Keep the same structure expected by
        # remediation_agent.py.
        "prompts": [
            {
                "canonical_id": (
                    canonical_id
                ),

                "context_id": (
                    original_prompt.get(
                        "context_id"
                    )
                ),

                "system_instructions": (
                    RETRY_SYSTEM_INSTRUCTIONS
                ),

                "user_prompt": (
                    retry_prompt
                ),
            }
        ],
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

    print("=" * 60)
    print("FixProof Retry Prompt Builder")
    print("=" * 60)

    print(
        f"Canonical finding: "
        f"{canonical_id}"
    )

    print("Attempt: 2")

    print(
        "Previous decision: "
        f"{result['retry']['previous_disposition']}"
    )

    print(
        f"Output: {output_file}"
    )

    return result


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Build a remediation retry prompt "
            "using independent FixProof "
            "validation evidence."
        )
    )

    parser.add_argument(
        "--original-prompts",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--remediation",
        required=True,
        type=Path,
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
        "--decision",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--canonical-id",
        required=True,
    )

    parser.add_argument(
        "--output",
        required=True,
        type=Path,
    )

    args = parser.parse_args()

    build_retry_prompt_file(
        original_prompt_file=(
            args.original_prompts.resolve()
        ),
        remediation_file=(
            args.remediation.resolve()
        ),
        preliminary_file=(
            args.preliminary.resolve()
        ),
        security_file=(
            args.security.resolve()
        ),
        functional_file=(
            args.functional.resolve()
        ),
        decision_file=(
            args.decision.resolve()
        ),
        canonical_id=(
            args.canonical_id
        ),
        output_file=(
            args.output.resolve()
        ),
    )


if __name__ == "__main__":
    main()