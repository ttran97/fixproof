from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable


DEFAULT_SEMGREP_TIMEOUT_SECONDS = 120


def build_semgrep_command(
    target: Path,
    output: Path,
    project_rule_dir: Path | None = None,
    additional_configs: Iterable[str | Path] | None = None,
) -> list[str]:
    """
    Build the Semgrep command used by FixProof.

    FixProof intentionally combines:

    1. Semgrep's standard OSS/default rule configuration.
    2. Local FixProof controlled evaluation rules.

    Local rules supplement the scanner; they do not replace
    independent ground truth.
    """

    command = [
        "semgrep",
        "scan",
        "--config",
        "auto",
    ]

    # -------------------------------------------------
    # FixProof controlled evaluation rules
    # -------------------------------------------------

    if (
        project_rule_dir is not None
        and project_rule_dir.exists()
    ):
        command.extend(
            [
                "--config",
                str(
                    project_rule_dir.resolve()
                ),
            ]
        )

    # -------------------------------------------------
    # Optional future configurations
    # -------------------------------------------------

    if additional_configs:

        for config in additional_configs:

            command.extend(
                [
                    "--config",
                    str(config),
                ]
            )

    command.extend(
        [
            "--json",
            "--output",
            str(output.resolve()),
            str(target),
        ]
    )

    return command


def run_semgrep(
    target: Path,
    output: Path,
    project_rule_dir: Path | None = None,
    additional_configs: Iterable[str | Path] | None = None,
    timeout_seconds: int = DEFAULT_SEMGREP_TIMEOUT_SECONDS,
) -> Path:
    """
    Execute Semgrep against a FixProof scan target.

    Return codes:

    0 = scan completed successfully
    1 = findings may have been produced depending on
        Semgrep configuration

    Any other code is considered a scanner execution failure.
    """

    target = Path(target)
    output = Path(output)

    if not target.exists():

        raise FileNotFoundError(
            f"Semgrep target does not exist: "
            f"{target}"
        )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Default project rule directory.
    #
    # This preserves the existing run_semgrep(target, output)
    # API used throughout FixProof.
    if project_rule_dir is None:

        project_rule_dir = Path(
            "rules"
        )

    command = build_semgrep_command(
        target=target,
        output=output,
        project_rule_dir=project_rule_dir,
        additional_configs=additional_configs,
    )

    print(
        "FixProof - Starting Semgrep scan"
    )

    print(
        f"Target: {target}"
    )

    print(
        f"Output: {output.resolve()}"
    )

    if (
        project_rule_dir is not None
        and project_rule_dir.exists()
    ):

        print(
            "FixProof rules: "
            f"{project_rule_dir.resolve()}"
        )

    print()

    #
    # Do not use capture_output=True here.
    #
    # Semgrep CLI output previously caused Windows
    # encoding issues in this environment.
    #
    if timeout_seconds <= 0:
        raise ValueError(
            "Semgrep timeout must be greater than zero seconds."
        )

    try:
        result = subprocess.run(
            command,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            "Semgrep execution exceeded the fixed process timeout of "
            f"{timeout_seconds} seconds."
        ) from exc

    if result.returncode not in (
        0,
        1,
    ):

        raise RuntimeError(
            "Semgrep execution failed "
            f"with return code "
            f"{result.returncode}."
        )

    if not output.exists():

        raise RuntimeError(
            "Semgrep completed but did not "
            f"produce output: {output}"
        )

    print()
    print(
        "FixProof - Semgrep scan completed"
    )

    print(
        "Raw results saved to: "
        f"{output.resolve()}"
    )

    return output


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Run Semgrep using both standard "
            "Semgrep rules and FixProof "
            "controlled evaluation rules."
        )
    )

    parser.add_argument(
        "--target",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--output",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--rules",
        default=Path("rules"),
        type=Path,
    )

    parser.add_argument(
        "--process-timeout",
        default=DEFAULT_SEMGREP_TIMEOUT_SECONDS,
        type=int,
        help="Maximum Semgrep process runtime in seconds.",
    )

    args = parser.parse_args()

    run_semgrep(
        target=args.target,
        output=args.output,
        project_rule_dir=args.rules,
        timeout_seconds=args.process_timeout,
    )
