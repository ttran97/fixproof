from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from openai import OpenAI
from pydantic import BaseModel

from fixproof.config import find_environment_file, load_environment_file


class RemediationResponse(BaseModel):
    canonical_id: str
    analysis: str
    remediation_strategy: str
    patched_code: str
    assumptions: list[str]
    needs_additional_context: bool


def load_prompt(
    prompt_file: Path,
    canonical_id: str,
) -> dict[str, Any]:
    data = json.loads(
        prompt_file.read_text(encoding="utf-8")
    )

    for prompt in data.get("prompts", []):
        if prompt.get("canonical_id") == canonical_id:
            return prompt

    raise ValueError(
        f"Canonical finding not found in prompt file: {canonical_id}"
    )


def run_remediation(
    prompt_file: Path,
    output_file: Path,
    canonical_id: str,
    model: str,
) -> dict[str, Any]:

    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError(
            "No OpenAI API key configured. Set OPENAI_API_KEY or add it "
            "to the local ignored .env file."
        )

    prompt = load_prompt(
        prompt_file=prompt_file,
        canonical_id=canonical_id,
    )

    client = OpenAI()

    print("=" * 60)
    print("FixProof AI Remediation Agent")
    print("=" * 60)
    print(f"Canonical finding: {canonical_id}")
    print(f"Model: {model}")
    print()

    response = client.responses.parse(
        model=model,
        instructions=prompt["system_instructions"],
        input=prompt["user_prompt"],
        text_format=RemediationResponse,
    )

    parsed = response.output_parsed

    if parsed is None:
        raise RuntimeError(
            "The model did not return a valid structured remediation."
        )

    # Safety/integrity check:
    # the model must return the same finding ID it was asked to remediate.
    if parsed.canonical_id != canonical_id:
        raise RuntimeError(
            "Model returned a different canonical_id. "
            f"Expected {canonical_id}, "
            f"received {parsed.canonical_id}"
        )

    result = {
        "schema_version": "0.1",
        "project": "FixProof",

        "remediation": {
            "canonical_id": canonical_id,
            "model": model,
            "response_id": response.id,

            "analysis": parsed.analysis,

            "remediation_strategy": (
                parsed.remediation_strategy
            ),

            "patched_code": parsed.patched_code,

            "assumptions": parsed.assumptions,

            "needs_additional_context": (
                parsed.needs_additional_context
            ),
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

    print("Candidate remediation generated.")
    print(f"Output: {output_file}")

    if parsed.needs_additional_context:
        print(
            "WARNING: Model indicated that additional "
            "source context is required."
        )

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate one candidate security remediation "
            "using the OpenAI API."
        )
    )

    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="FixProof prompt JSON file.",
    )

    parser.add_argument(
        "--canonical-id",
        required=True,
        help="Canonical FixProof finding to remediate.",
    )

    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Remediation JSON output.",
    )

    parser.add_argument(
        "--model",
        help=(
            "OpenAI model to use. "
            "Can also be configured with FIXPROOF_MODEL in the shell or .env."
        ),
    )

    parser.add_argument(
        "--env-file",
        type=Path,
        help=(
            "Local environment file. Defaults to the nearest .env found "
            "from the prompt file toward the filesystem root."
        ),
    )

    args = parser.parse_args()

    if args.env_file is not None:
        load_environment_file(args.env_file, required=True)
    else:
        environment_file = find_environment_file(args.input.parent)
        if environment_file is not None:
            load_environment_file(environment_file)

    model = args.model or os.getenv("FIXPROOF_MODEL")

    if not model:
        raise ValueError(
            "No model configured. Supply --model or "
            "set FIXPROOF_MODEL in the shell or local .env file."
        )

    run_remediation(
        prompt_file=args.input,
        output_file=args.output,
        canonical_id=args.canonical_id,
        model=model,
    )


if __name__ == "__main__":
    main()
