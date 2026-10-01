from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from fixproof.evaluation.path_s06_extension import (
    PROTOCOL_ID,
    read_json,
    resolve_inside,
    sha256_file,
    verify_run,
    write_json,
)
from fixproof.evaluation.supplemental_followup import verify_recorded_follow_ups


RUN_ID = "20260930T180925912688Z-path-s06-v1"
APPROVAL = Path("data/extensions/path-s06-v1/human-review-approval.json")
REVIEW_ROOT = Path("data/extensions/path-s06-v1/human-reviews")
WORKSHEET = Path(
    "docs/coursework/review-2026-09-30/PATH-S06-extension-human-review.md"
)
TARGETS = tuple(
    f"primary-v1-path-traversal-initial-{attempt:02d}"
    for attempt in range(1, 6)
)
EXPECTED_PRIOR_VERDICTS = {
    TARGETS[0]: "FOLLOW_UP_REJECT_CANDIDATE",
    **{
        trial_id: "FOLLOW_UP_REQUEST_MORE_TESTING"
        for trial_id in TARGETS[1:]
    },
}
VERDICT = "FOLLOW_UP_REJECT_CANDIDATE"
REQUIRED_CHECK_KEYS = {
    "reviewed_frozen_protocol",
    "reviewed_baseline_gate",
    "reviewed_run_summary",
    "reviewed_all_five_candidate_results",
    "manually_reproduced_traversal_02",
    "preserve_primary_v1",
    "preserve_supplemental_v1",
}


def binding(project_root: Path, relative: str | Path) -> dict[str, str]:
    relative_path = Path(relative)
    path = resolve_inside(project_root, relative_path)
    if not path.is_file():
        raise FileNotFoundError(f"Extension review evidence is missing: {path}")
    return {
        "path": relative_path.as_posix(),
        "sha256": sha256_file(path),
    }


def load_approval(project_root: Path) -> dict[str, Any]:
    approval = read_json(resolve_inside(project_root, APPROVAL))
    if approval.get("protocol_id") != PROTOCOL_ID:
        raise ValueError("Extension approval has the wrong protocol ID.")
    if approval.get("status") != "confirmed":
        raise ValueError("Extension approval is not confirmed.")
    if approval.get("reviewer") != "Tony Tran":
        raise ValueError("Extension approval has an unexpected reviewer.")
    checks = approval.get("confirmed_checks") or {}
    if set(checks) != REQUIRED_CHECK_KEYS or not all(checks.values()):
        raise ValueError("Extension approval checks are incomplete.")
    decisions = approval.get("decisions") or []
    if {row.get("trial_id") for row in decisions} != set(TARGETS):
        raise ValueError("Extension approval must contain exactly five targets.")
    for decision in decisions:
        if decision.get("verdict") != VERDICT:
            raise ValueError("Every approved PATH-S06 verdict must be rejection.")
        if len(str(decision.get("rationale", "")).strip()) < 120:
            raise ValueError("Each extension rationale must be evidence-specific.")
        expected_manual = decision["trial_id"] == TARGETS[1]
        if decision.get("manual_reproduction") is not expected_manual:
            raise ValueError("Only Traversal 02 was manually reproduced.")
    return approval


def prior_follow_up_path(trial_id: str) -> Path:
    return Path("data/supplemental/v1/follow-up-reviews") / trial_id / "result.json"


def packet_path(trial_id: str) -> Path:
    return REVIEW_ROOT / trial_id / "packet.json"


def result_path(trial_id: str) -> Path:
    return REVIEW_ROOT / trial_id / "result.json"


def candidate_row(summary: dict[str, Any], trial_id: str) -> dict[str, Any]:
    matches = [
        row for row in summary.get("candidate_results", [])
        if row.get("target_id") == trial_id
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected one extension result for {trial_id}.")
    return matches[0]


def build_packet(project_root: Path, trial_id: str) -> dict[str, Any]:
    if trial_id not in TARGETS:
        raise ValueError(f"Not a PATH-S06 extension review target: {trial_id}")
    summary = verify_run(project_root, RUN_ID)
    extension_row = candidate_row(summary, trial_id)
    candidate_result = read_json(
        resolve_inside(project_root, extension_row["result"])
    )
    evaluation = candidate_result.get("evaluation") or {}
    response = candidate_result.get("response") or {}
    if (
        evaluation.get("status") != "fail"
        or evaluation.get("marker_disclosed") is not True
        or response.get("status_code") != 200
    ):
        raise ValueError(f"Unexpected PATH-S06 evidence for {trial_id}.")

    prior_path = prior_follow_up_path(trial_id)
    prior = read_json(resolve_inside(project_root, prior_path))
    if prior.get("verdict") != EXPECTED_PRIOR_VERDICTS[trial_id]:
        raise ValueError(f"Unexpected prior follow-up verdict for {trial_id}.")
    prior_packet = read_json(
        resolve_inside(project_root, prior["packet"]["path"])
    )
    patch = prior_packet["candidate_patch"]
    if binding(project_root, patch["path"])["sha256"] != patch["sha256"]:
        raise ValueError(f"Candidate patch binding changed for {trial_id}.")

    return {
        "schema_version": "0.1",
        "project": "FixProof",
        "artifact_type": "path_s06_extension_follow_up_review_packet",
        "protocol_id": PROTOCOL_ID,
        "status": "evidence_ready_for_confirmed_review",
        "trial_id": trial_id,
        "case_id": "PATH-S06",
        "purpose": (
            "Bind the frozen PATH-S06 extension result to the candidate's prior "
            "follow-up without modifying either earlier record."
        ),
        "protocol_lock": binding(
            project_root, "data/extensions/path-s06-v1/protocol-lock.json"
        ),
        "extension_run_summary": binding(
            project_root,
            f"data/extensions/path-s06-v1/runs/{RUN_ID}/summary.json",
        ),
        "extension_candidate_result": {
            "path": extension_row["result"],
            "sha256": extension_row["sha256"],
            "status": extension_row["status"],
            "status_code": extension_row["status_code"],
            "marker_disclosed": extension_row["marker_disclosed"],
        },
        "prior_supplemental_follow_up": {
            **binding(project_root, prior_path),
            "verdict": prior["verdict"],
            "reviewed_at": prior["reviewed_at"],
        },
        "candidate_patch": patch,
        "review_worksheet": binding(project_root, WORKSHEET),
        "required_review_checks": [
            "Reviewed the frozen PATH-S06 protocol and baseline gate.",
            "Reviewed the registered run summary and this candidate result.",
            "Compared the extension result with the preserved prior follow-up.",
            "Distinguished a registered security disclosure from status-only failure.",
            "Confirmed that primary-v1 and supplemental-v1 remain unchanged.",
        ],
        "allowed_verdicts": [VERDICT],
        "decision_boundary": (
            "The extension qualifies the current human conclusion but does not "
            "replace primary-v1, supplemental-v1, or an earlier human record."
        ),
        "effect_on_frozen_records": "none_earlier_records_are_preserved",
    }


def initialize_packets(project_root: Path) -> list[Path]:
    created: list[Path] = []
    for trial_id in TARGETS:
        path = resolve_inside(project_root, packet_path(trial_id))
        packet = build_packet(project_root, trial_id)
        if path.is_file():
            if read_json(path) != packet:
                raise ValueError(f"Existing extension review packet is stale: {path}")
        else:
            write_json(path, packet)
        created.append(path)
    return created


def record_approved_reviews(project_root: Path) -> list[Path]:
    approval = load_approval(project_root)
    decisions = {row["trial_id"]: row for row in approval["decisions"]}
    approval_binding = binding(project_root, APPROVAL)
    recorded: list[Path] = []
    for trial_id in TARGETS:
        packet_file = resolve_inside(project_root, packet_path(trial_id))
        if not packet_file.is_file():
            raise FileNotFoundError(f"Extension review packet is missing: {packet_file}")
        packet = read_json(packet_file)
        if packet != build_packet(project_root, trial_id):
            raise ValueError(f"Extension review packet is stale: {packet_file}")
        decision = decisions[trial_id]
        result = {
            "schema_version": "0.1",
            "project": "FixProof",
            "artifact_type": "path_s06_extension_follow_up_review_result",
            "protocol_id": PROTOCOL_ID,
            "status": "completed",
            "trial_id": trial_id,
            "reviewer": approval["reviewer"],
            "reviewed_at": approval["approved_at"],
            "verdict": decision["verdict"],
            "rationale": decision["rationale"],
            "manual_reproduction": decision["manual_reproduction"],
            "relationship_to_prior_follow_up": decision[
                "relationship_to_prior_follow_up"
            ],
            "confirmed_required_checks": True,
            "approval": approval_binding,
            "packet": binding(project_root, packet_path(trial_id)),
            "extension_candidate_result": packet["extension_candidate_result"],
            "prior_supplemental_follow_up": packet[
                "prior_supplemental_follow_up"
            ],
            "effect_on_frozen_records": "none_earlier_records_are_preserved",
        }
        output = resolve_inside(project_root, result_path(trial_id))
        if output.is_file():
            if read_json(output) != result:
                raise ValueError(f"Existing extension review result differs: {output}")
        else:
            write_json(output, result)
        recorded.append(output)
    return recorded


def verify_extension_follow_ups(project_root: Path) -> dict[str, int]:
    summary = verify_run(project_root, RUN_ID)
    approval = load_approval(project_root)
    decisions = {row["trial_id"]: row for row in approval["decisions"]}
    approval_binding = binding(project_root, APPROVAL)
    completed = 0
    for trial_id in TARGETS:
        packet_file = resolve_inside(project_root, packet_path(trial_id))
        result_file = resolve_inside(project_root, result_path(trial_id))
        packet = read_json(packet_file)
        if packet != build_packet(project_root, trial_id):
            raise ValueError(f"Extension packet failed reconstruction: {packet_file}")
        result = read_json(result_file)
        decision = decisions[trial_id]
        if result.get("status") != "completed":
            raise ValueError(f"Extension result is incomplete: {result_file}")
        if result.get("verdict") != VERDICT:
            raise ValueError(f"Extension verdict is invalid: {result_file}")
        if result.get("rationale") != decision["rationale"]:
            raise ValueError(f"Extension rationale changed: {result_file}")
        if result.get("manual_reproduction") is not decision["manual_reproduction"]:
            raise ValueError(f"Manual-reproduction claim changed: {result_file}")
        if result.get("approval") != approval_binding:
            raise ValueError(f"Extension approval binding changed: {result_file}")
        if result.get("packet") != binding(project_root, packet_path(trial_id)):
            raise ValueError(f"Extension packet binding changed: {result_file}")
        row = candidate_row(summary, trial_id)
        if result.get("extension_candidate_result") != packet.get(
            "extension_candidate_result"
        ) or row.get("sha256") != packet["extension_candidate_result"]["sha256"]:
            raise ValueError(f"Extension candidate binding changed: {result_file}")
        if result.get("prior_supplemental_follow_up") != packet.get(
            "prior_supplemental_follow_up"
        ):
            raise ValueError(f"Prior follow-up binding changed: {result_file}")
        if result.get("effect_on_frozen_records") != (
            "none_earlier_records_are_preserved"
        ):
            raise ValueError(f"Frozen-record boundary changed: {result_file}")
        completed += 1

    prior = verify_recorded_follow_ups(project_root)
    if prior != {"registered_targets": 14, "completed": 14, "pending": 0}:
        raise ValueError("The preserved supplemental-v1 follow-up set changed.")
    return {"registered_targets": len(TARGETS), "completed": completed}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Record or verify PATH-S06 extension human qualifications."
    )
    parser.add_argument(
        "command", choices=("initialize", "record-approved", "verify")
    )
    parser.add_argument("--project-root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.project_root.resolve()

    if args.command == "initialize":
        paths = initialize_packets(root)
        print(f"PATH-S06 review packets ready: {len(paths)}/{len(TARGETS)}")
        return
    if args.command == "record-approved":
        paths = record_approved_reviews(root)
        print(f"PATH-S06 human qualifications recorded: {len(paths)}/{len(TARGETS)}")
        return
    result = verify_extension_follow_ups(root)
    print(
        "PATH-S06 human qualifications verified: "
        f"{result['completed']}/{result['registered_targets']} complete"
    )


if __name__ == "__main__":
    main()
