from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any


LINE_PREFIX_PATTERN = re.compile(
    r"^(?:>>|\s*)\s*\d+:\s?(.*)$"
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def sha256_text(value: str) -> str:
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


def find_context(
    context_data: dict[str, Any],
    canonical_id: str,
) -> dict[str, Any]:

    for context in context_data.get(
        "contexts",
        [],
    ):
        if (
            context.get("canonical_id")
            == canonical_id
        ):
            return context

    raise ValueError(
        f"Context not found for {canonical_id}"
    )


def remove_context_markers(
    source_context: str,
) -> str:
    """
    Convert context such as:

       9: app.get(...)
    >> 11: vulnerable_line

    back into the original source code.
    """

    clean_lines = []

    for line in source_context.splitlines():

        match = LINE_PREFIX_PATTERN.match(
            line
        )

        if not match:
            raise ValueError(
                "Could not parse context line: "
                f"{line}"
            )

        clean_lines.append(
            match.group(1)
        )

    return "\n".join(
        clean_lines
    )


def create_patch_workspace(
    project_root: Path,
    context_file: Path,
    remediation_file: Path,
    workspace_root: Path,
    attempt: int,
) -> dict[str, Any]:

    if attempt < 1:
        raise ValueError(
            "Attempt number must be >= 1."
        )

    context_data = load_json(
        context_file
    )

    remediation_data = load_json(
        remediation_file
    )

    remediation = remediation_data[
        "remediation"
    ]

    canonical_id = remediation[
        "canonical_id"
    ]

    context = find_context(
        context_data=context_data,
        canonical_id=canonical_id,
    )

    source_relative = Path(
        context[
            "location"
        ]["file"].replace(
            "\\",
            "/",
        )
    )

    source_file = (
        project_root
        / source_relative
    ).resolve()

    if not source_file.exists():
        raise FileNotFoundError(
            "Original source file not found: "
            f"{source_file}"
        )

    source_app_root = (
        source_file.parent
    )

    #
    # Attempt-specific workspace.
    #
    # Example:
    #
    # workspaces/
    #   CF-ffcaa5bd5497/
    #       attempt-02/
    #
    finding_workspace = (
        workspace_root
        / canonical_id
    )

    workspace_dir = (
        finding_workspace
        / f"attempt-{attempt:02d}"
    )

    workspace_app = (
        workspace_dir
        / "app"
    )

    #
    # Re-running the same attempt starts from
    # a deterministic fresh workspace.
    #
    if workspace_dir.exists():

        shutil.rmtree(
            workspace_dir
        )

    workspace_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    shutil.copytree(
        source_app_root,
        workspace_app,
        ignore=shutil.ignore_patterns(
            "node_modules",
            ".git",
            "__pycache__",
        ),
    )

    workspace_source = (
        workspace_app
        / source_file.name
    )

    original_file_text = (
        workspace_source.read_text(
            encoding="utf-8"
        )
    )

    original_context = (
        remove_context_markers(
            context[
                "source_context"
            ]["code"]
        )
    )

    patched_code = remediation.get(
        "patched_code",
        "",
    ).strip()

    if not patched_code:
        raise ValueError(
            "AI remediation contains "
            "empty patched_code."
        )

    occurrence_count = (
        original_file_text.count(
            original_context
        )
    )

    if occurrence_count != 1:
        raise RuntimeError(
            "Expected the original source "
            "context to occur exactly once, "
            f"but found {occurrence_count}."
        )

    #
    # Apply only the AI-generated candidate.
    #
    patched_file_text = (
        original_file_text.replace(
            original_context,
            patched_code,
            1,
        )
    )

    workspace_source.write_text(
        patched_file_text,
        encoding="utf-8",
    )

    #
    # Generate auditable unified diff.
    #
    diff = "".join(
        difflib.unified_diff(
            original_file_text.splitlines(
                keepends=True
            ),
            patched_file_text.splitlines(
                keepends=True
            ),
            fromfile=(
                f"original/{source_file.name}"
            ),
            tofile=(
                f"candidate/{source_file.name}"
            ),
        )
    )

    diff_file = (
        workspace_dir
        / "candidate.patch"
    )

    diff_file.write_text(
        diff,
        encoding="utf-8",
    )

    metadata = {
        "schema_version": "0.2",
        "project": "FixProof",

        "patch_workspace": {
            "canonical_id": (
                canonical_id
            ),

            "attempt": attempt,

            "original_source": str(
                source_file
            ),

            "workspace_source": str(
                workspace_source.resolve()
            ),

            "workspace_directory": str(
                workspace_dir.resolve()
            ),

            "patch_file": str(
                diff_file.resolve()
            ),

            "remediation_file": str(
                remediation_file.resolve()
            ),

            "model": remediation.get(
                "model"
            ),

            "response_id": remediation.get(
                "response_id"
            ),

            "hashes": {
                "original_source_sha256": (
                    sha256_text(
                        original_file_text
                    )
                ),

                "candidate_source_sha256": (
                    sha256_text(
                        patched_file_text
                    )
                ),

                "patch_sha256": (
                    sha256_text(
                        diff
                    )
                ),
            },

            "original_modified": False,

            "status": (
                "candidate_applied"
            ),
        },
    }

    metadata_file = (
        workspace_dir
        / "workspace.json"
    )

    metadata_file.write_text(
        json.dumps(
            metadata,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("=" * 60)
    print("FixProof Patch Workspace")
    print("=" * 60)

    print(
        f"Canonical finding: "
        f"{canonical_id}"
    )

    print(
        f"Attempt: {attempt}"
    )

    print(
        f"Original source: "
        f"{source_file}"
    )

    print(
        f"Candidate source: "
        f"{workspace_source}"
    )

    print(
        f"Patch diff: "
        f"{diff_file}"
    )

    print(
        f"Workspace metadata: "
        f"{metadata_file}"
    )

    print()
    print(
        "Original application was not modified."
    )

    return metadata


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Create an isolated FixProof "
            "candidate-patch workspace."
        )
    )

    parser.add_argument(
        "--contexts",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--remediation",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--attempt",
        required=True,
        type=int,
        help=(
            "Remediation attempt number."
        ),
    )

    parser.add_argument(
        "--project-root",
        default=Path("."),
        type=Path,
    )

    parser.add_argument(
        "--workspace-root",
        default=Path("workspaces"),
        type=Path,
    )

    args = parser.parse_args()

    create_patch_workspace(
        project_root=(
            args.project_root.resolve()
        ),

        context_file=(
            args.contexts.resolve()
        ),

        remediation_file=(
            args.remediation.resolve()
        ),

        workspace_root=(
            args.workspace_root.resolve()
        ),

        attempt=args.attempt,
    )


if __name__ == "__main__":
    main()