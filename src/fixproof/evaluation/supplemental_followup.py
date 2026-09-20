from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from fixproof.evaluation.supplemental_protocol import (
    load_json,
    resolve_project_path,
    sha256_file,
    write_json,
)
from fixproof.evaluation.supplemental_runner import utc_now
from fixproof.evaluation.supplemental_report import (
    build_supplemental_report,
)


FOLLOW_UP_TARGETS = {
    "primary-v1-xss-initial-04": ("xss", 4),
    "primary-v1-xss-initial-05": ("xss", 5),
    "primary-v1-path-traversal-initial-01": ("path-traversal", 1),
}

ALLOWED_VERDICTS = (
    "FOLLOW_UP_ACCEPT_CANDIDATE",
    "FOLLOW_UP_REJECT_CANDIDATE",
    "FOLLOW_UP_REQUEST_MORE_TESTING",
)

REQUIRED_CHECKS = (
    "Reviewed the original candidate patch and original adjudication rationale.",
    "Reviewed every supplemental case, input, observed response, and oracle outcome for this candidate.",
    "Distinguished security, behavioral-parity, robustness, and inconclusive evidence.",
    "Compared the candidate with the other saved candidates evaluated under the same CWE protocol.",
    "Confirmed that this follow-up does not overwrite or retroactively alter primary-v1 metrics.",
)


def _binding(project_root: Path, relative_path: str) -> dict[str, str]:
    path = resolve_project_path(project_root, relative_path)
    if not path.is_file():
        raise FileNotFoundError(f"Follow-up evidence not found: {path}")
    return {"path": relative_path, "sha256": sha256_file(path)}


def _find_primary_trial(
    primary_report: dict[str, Any],
    trial_id: str,
) -> dict[str, Any]:
    for row in primary_report["experiment_matrix"]:
        if row.get("trial_id") == trial_id:
            return row
    raise ValueError(f"Primary trial not found: {trial_id}")


def build_follow_up_packet(
    project_root: Path,
    trial_id: str,
) -> dict[str, Any]:
    if trial_id not in FOLLOW_UP_TARGETS:
        raise ValueError(f"Not a registered follow-up target: {trial_id}")
    cwe, attempt = FOLLOW_UP_TARGETS[trial_id]
    root = project_root.resolve()

    report_path = "data/supplemental/v1/supplemental-report.json"
    stored_report = load_json(resolve_project_path(root, report_path))
    rebuilt_report = build_supplemental_report(root, bound_report=stored_report)
    if stored_report != rebuilt_report:
        raise ValueError("Stored supplemental report is stale or inconsistent.")

    cwe_result = next(
        row for row in stored_report["cwes"] if row["cwe_case"] == cwe
    )
    candidate = next(
        row for row in cwe_result["candidates"] if row["attempt"] == attempt
    )

    primary_report_path = "data/evaluation/primary-report.json"
    primary_report = load_json(resolve_project_path(root, primary_report_path))
    primary_trial = _find_primary_trial(primary_report, trial_id)
    if primary_trial["adjudication"]["verdict"] != "REQUEST_ADDITIONAL_TESTING":
        raise ValueError(
            f"Primary review does not request additional testing: {trial_id}"
        )

    original_result = primary_trial["artifacts"]["adjudication_result"]
    patch = primary_trial["artifacts"]["patch"]
    for bound in (original_result, patch):
        actual = _binding(root, bound["path"])
        if actual["sha256"] != bound["sha256"]:
            raise ValueError(
                f"Primary evidence binding mismatch: {bound['path']}"
            )

    comparable = []
    for row in cwe_result["candidates"]:
        comparable.append(
            {
                "attempt": row["attempt"],
                "summary": row["summary"],
                "nonpassing_tests": row["nonpassing_tests"],
            }
        )

    return {
        "schema_version": "0.1",
        "project": "FixProof",
        "artifact_type": "supplemental_follow_up_review_packet",
        "protocol_id": "supplemental-v1",
        "status": "pending_human_review",
        "trial_id": trial_id,
        "cwe_case": cwe,
        "attempt": attempt,
        "purpose": (
            "Record a dated human conclusion after the requested supplemental "
            "testing without overwriting the original primary review."
        ),
        "original_primary_review": {
            "verdict": primary_trial["adjudication"]["verdict"],
            "reviewer": primary_trial["adjudication"]["reviewer"],
            "reviewed_at": primary_trial["adjudication"]["reviewed_at"],
            "rationale": primary_trial["adjudication"]["rationale"],
            "result": original_result,
        },
        "candidate_patch": patch,
        "supplemental_report": _binding(root, report_path),
        "supplemental_candidate_result": {
            "path": candidate["path"],
            "sha256": candidate["sha256"],
            "summary": candidate["summary"],
            "nonpassing_tests": candidate["nonpassing_tests"],
        },
        "comparable_candidate_context": comparable,
        "required_review_checks": list(REQUIRED_CHECKS),
        "allowed_verdicts": list(ALLOWED_VERDICTS),
        "decision_boundary": (
            "A passing security subset does not erase a parity or robustness "
            "failure. An inconclusive case must remain inconclusive. The human "
            "reviewer decides whether the complete bounded evidence supports "
            "acceptance, rejection, or further testing."
        ),
        "effect_on_primary_record": "none_original_record_is_preserved",
    }


def initialize_packets(project_root: Path) -> list[Path]:
    root = project_root.resolve()
    created = []
    for trial_id in FOLLOW_UP_TARGETS:
        packet = build_follow_up_packet(root, trial_id)
        path = (
            root
            / "data/supplemental/v1/follow-up-reviews"
            / trial_id
            / "packet.json"
        )
        if path.is_file():
            if load_json(path) != packet:
                raise ValueError(f"Existing follow-up packet is stale: {path}")
        else:
            write_json(path, packet)
        created.append(path)
    return created


def verify_packet_bindings(
    project_root: Path,
    packet: dict[str, Any],
) -> None:
    if packet.get("protocol_id") != "supplemental-v1":
        raise ValueError("Follow-up packet has the wrong protocol ID.")
    if packet.get("status") != "pending_human_review":
        raise ValueError("Follow-up packet is not pending human review.")
    bindings = [
        packet["original_primary_review"]["result"],
        packet["candidate_patch"],
        packet["supplemental_report"],
        packet["supplemental_candidate_result"],
    ]
    for binding in bindings:
        actual = _binding(project_root, binding["path"])
        if actual["sha256"] != binding["sha256"]:
            raise ValueError(f"Evidence hash mismatch: {binding['path']}")


def ensure_follow_up_path(project_root: Path, path: Path) -> Path:
    root = project_root.resolve()
    resolved = path.resolve()
    allowed = (root / "data/supplemental/v1/follow-up-reviews").resolve()
    try:
        resolved.relative_to(allowed)
    except ValueError as exc:
        raise ValueError(
            "Follow-up packet and result paths must stay under "
            "data/supplemental/v1/follow-up-reviews."
        ) from exc
    return resolved


def record_follow_up(
    project_root: Path,
    packet_path: Path,
    output_path: Path,
    reviewer: str,
    verdict: str,
    rationale: str,
    confirm_all_required_checks: bool,
) -> dict[str, Any]:
    if verdict not in ALLOWED_VERDICTS:
        raise ValueError(f"Unsupported follow-up verdict: {verdict}")
    if not reviewer.strip():
        raise ValueError("Reviewer must be nonempty.")
    if len(rationale.strip()) < 40:
        raise ValueError("Follow-up rationale must be evidence-based and specific.")
    if not confirm_all_required_checks:
        raise ValueError("All required follow-up review checks must be confirmed.")
    if output_path.exists():
        raise FileExistsError(
            "Follow-up result already exists and will not be overwritten: "
            f"{output_path}"
        )

    packet_path = ensure_follow_up_path(project_root, packet_path)
    output_path = ensure_follow_up_path(project_root, output_path)
    packet = load_json(packet_path)
    verify_packet_bindings(project_root.resolve(), packet)
    result = {
        "schema_version": "0.1",
        "project": "FixProof",
        "artifact_type": "supplemental_follow_up_review_result",
        "protocol_id": "supplemental-v1",
        "status": "completed",
        "trial_id": packet["trial_id"],
        "reviewer": reviewer.strip(),
        "reviewed_at": utc_now(),
        "verdict": verdict,
        "rationale": rationale.strip(),
        "confirmed_required_checks": True,
        "packet": {
            "path": str(
                packet_path.resolve().relative_to(project_root.resolve())
            ).replace("\\", "/"),
            "sha256": sha256_file(packet_path),
        },
        "supplemental_candidate_result": packet[
            "supplemental_candidate_result"
        ],
        "effect_on_primary_record": "none_original_record_is_preserved",
    }
    write_json(output_path, result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Initialize or record FixProof supplemental follow-up reviews."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    initialize = subparsers.add_parser("initialize")
    initialize.add_argument("--project-root", type=Path, default=Path("."))

    record = subparsers.add_parser("record")
    record.add_argument("--project-root", type=Path, default=Path("."))
    record.add_argument("--packet", type=Path, required=True)
    record.add_argument("--output", type=Path, required=True)
    record.add_argument("--reviewer", required=True)
    record.add_argument("--verdict", choices=ALLOWED_VERDICTS, required=True)
    record.add_argument("--rationale-file", type=Path, required=True)
    record.add_argument("--confirm-all-required-checks", action="store_true")

    args = parser.parse_args()
    root = args.project_root.resolve()
    if args.command == "initialize":
        for path in initialize_packets(root):
            print(path.relative_to(root))
        return

    packet = args.packet if args.packet.is_absolute() else root / args.packet
    output = args.output if args.output.is_absolute() else root / args.output
    rationale_file = (
        args.rationale_file
        if args.rationale_file.is_absolute()
        else root / args.rationale_file
    )
    rationale = rationale_file.read_text(encoding="utf-8-sig")
    result = record_follow_up(
        root,
        packet.resolve(),
        output.resolve(),
        args.reviewer,
        args.verdict,
        rationale,
        args.confirm_all_required_checks,
    )
    print(
        f"Follow-up result recorded for {result['trial_id']}: "
        f"{result['verdict']}"
    )


if __name__ == "__main__":
    main()
