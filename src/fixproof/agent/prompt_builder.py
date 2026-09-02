from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SYSTEM_INSTRUCTIONS = """
You are the remediation component of FixProof, a security patch
generation system.

Your job is to propose a minimal candidate remediation for exactly one
static-analysis finding.

Requirements:

1. Address only the supplied security finding.
2. Preserve the application's intended behavior whenever possible.
3. Do not modify unrelated functionality.
4. Do not add new security weaknesses.
5. Do not disable, suppress, ignore, or bypass the security scanner.
6. Do not remove functionality merely to make the finding disappear.
7. Do not assume the scanner finding is automatically correct.
8. Base the remediation only on the supplied evidence and source context.
9. Prefer a minimal source-code change.
10. The proposed patch will be independently validated after generation.

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


def build_prompt(context: dict[str, Any]) -> str:
    finding = context["finding"]
    location = context["location"]
    scanner_evidence = context["scanner_evidence"]
    source_context = context["source_context"]

    messages = scanner_evidence.get("messages", [])
    rules = scanner_evidence.get("rules", [])

    evidence_text = "\n".join(
        f"- {message}"
        for message in messages
        if message
    )

    if not evidence_text:
        evidence_text = "- No scanner explanation available."

    rule_text = "\n".join(
        "- "
        f"{rule.get('rule_id') or 'unknown rule'} "
        "(origin: "
        f"{rule.get('rule_origin', 'unknown')})"
        for rule in rules
    )

    if not rule_text:
        rule_text = "- No scanner rule details available."

    return f"""
FIXPROOF REMEDIATION TASK

Canonical Finding ID:
{context["canonical_id"]}

Language:
{location.get("language", "unknown")}

File:
{location.get("file")}

Affected Lines:
{location.get("start_line")} - {location.get("end_line")}

CWE:
{finding.get("cwe") or "Unknown"}

CWE Name:
{finding.get("cwe_name") or "Unknown"}

Vulnerability Class:
{finding.get("vulnerability_class") or "Unknown"}

Scanner Evidence Count:
{scanner_evidence.get("finding_count", 0)}

Scanner Rules and Origins:
{rule_text}

Scanner Explanations:
{evidence_text}

Source Context Type:
{source_context.get("context_type", "unknown")}

SOURCE CODE:
------------------------------
{source_context.get("code", "")}
------------------------------

Produce one minimal candidate remediation for this canonical finding.

The patched_code field must contain the complete replacement for the
source context shown above, without line-number prefixes or >> markers.

Do not attempt to validate your own patch. FixProof will perform
independent validation after generation.
""".strip()


def build_prompts(
    input_file: Path,
    output_file: Path,
) -> dict[str, Any]:

    context_data = json.loads(
        input_file.read_text(encoding="utf-8")
    )

    prompts = []

    for context in context_data.get("contexts", []):
        prompts.append(
            {
                "canonical_id": context["canonical_id"],
                "context_id": context["context_id"],
                "system_instructions": SYSTEM_INSTRUCTIONS,
                "user_prompt": build_prompt(context),
            }
        )

    result = {
        "schema_version": "0.1",
        "project": "FixProof",
        "prompt_build": {
            "contexts_received": len(
                context_data.get("contexts", [])
            ),
            "prompts_created": len(prompts),
        },
        "prompts": prompts,
    }

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file.write_text(
        json.dumps(result, indent=2),
        encoding="utf-8",
    )

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Build deterministic remediation prompts "
            "from FixProof contexts."
        )
    )

    parser.add_argument(
        "--input",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--output",
        required=True,
        type=Path,
    )

    args = parser.parse_args()

    result = build_prompts(
        input_file=args.input,
        output_file=args.output,
    )

    print("FixProof Prompt Builder")
    print(
        "Contexts received: "
        f"{result['prompt_build']['contexts_received']}"
    )
    print(
        "Prompts created: "
        f"{result['prompt_build']['prompts_created']}"
    )
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
