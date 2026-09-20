from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from fixproof.evaluation.supplemental_protocol import (
    DEFAULT_CASES,
    load_json,
    resolve_project_path,
    sha256_file,
    verify_definition,
    write_json,
)
from fixproof.evaluation.supplemental_runner import (
    latest_successful_baseline,
    summarize_candidate_cases,
)


CWE_ORDER = ("xss", "path-traversal", "sqli")
RUNS_ROOT = Path("data/supplemental/v1/runs")


def _relative(project_root: Path, path: Path) -> str:
    return str(path.resolve().relative_to(project_root.resolve())).replace(
        "\\", "/"
    )


def _verify_bound_run(
    project_root: Path,
    binding: dict[str, str],
    cwe: str,
    kind: str,
    filename: str,
) -> tuple[Path, dict[str, str]]:
    """Resolve one saved run without selecting a later reproducibility run."""
    root = project_root.resolve()
    path = resolve_project_path(root, binding["path"])
    runs_root = (root / RUNS_ROOT).resolve()
    try:
        relative = path.relative_to(runs_root)
    except ValueError as exc:
        raise ValueError(f"Bound run is outside supplemental runs: {path}") from exc
    if (
        len(relative.parts) != 2
        or relative.parts[0] != binding["run_id"]
        or not relative.parts[0].endswith(f"-{kind}-{cwe}")
        or relative.parts[1] != filename
    ):
        raise ValueError(f"Bound run path does not match {kind} {cwe}: {path}")
    if sha256_file(path) != binding["sha256"]:
        raise ValueError(f"Bound run hash mismatch: {path}")
    return path, {
        "path": _relative(root, path),
        "sha256": sha256_file(path),
        "run_id": binding["run_id"],
    }


def latest_completed_candidate_group(
    project_root: Path,
    cwe: str,
) -> Path:
    runs = project_root.resolve() / "data/supplemental/v1/runs"
    for path in sorted(
        runs.glob(f"*-candidates-{cwe}/summary.json"),
        reverse=True,
    ):
        result = load_json(path)
        if (
            result.get("protocol_id") == "supplemental-v1"
            and result.get("status") == "completed"
            and result.get("candidate_count") == 5
        ):
            return path
    raise FileNotFoundError(
        f"No completed supplemental candidate group exists for {cwe}."
    )


def _empty_counts() -> dict[str, int]:
    return {"total": 0, "pass": 0, "fail": 0, "inconclusive": 0}


def _add_counts(
    destination: dict[str, int],
    source: dict[str, int],
) -> None:
    for key in ("total", "pass", "fail", "inconclusive"):
        destination[key] += int(source[key])


def verify_baseline_result(
    project_root: Path,
    cwe: str,
    expected_ids: list[str],
    bound_binding: dict[str, str] | None = None,
) -> tuple[dict[str, str], dict[str, Any]]:
    if bound_binding is None:
        binding = latest_successful_baseline(project_root, cwe)
        path = resolve_project_path(project_root, binding["path"])
    else:
        path, binding = _verify_bound_run(
            project_root, bound_binding, cwe, "baseline", "result.json"
        )
    result = load_json(path)
    if (
        result.get("protocol_id") != "supplemental-v1"
        or result.get("cwe_case") != cwe
        or result.get("run_id") != binding["run_id"]
    ):
        raise ValueError(f"Baseline identity mismatch for {cwe}: {path}")
    if result.get("status") != "baseline_characterized":
        raise ValueError(f"Baseline is not characterized: {binding['path']}")
    ids = [case.get("test_id") for case in result.get("cases", [])]
    if ids != expected_ids:
        raise ValueError(f"Baseline test IDs differ for {cwe}.")
    statuses = [
        case["baseline_expectation_evaluation"]["status"]
        for case in result["cases"]
    ]
    recomputed = {
        "registered": len(statuses),
        "matched": statuses.count("match"),
        "mismatched": statuses.count("mismatch"),
        "inconclusive": statuses.count("inconclusive"),
        "candidate_execution_permitted": statuses.count("mismatch") == 0,
    }
    if result.get("summary") != recomputed:
        raise ValueError(f"Baseline summary does not recompute for {cwe}.")

    source_path = Path(result["preparation"]["source_app"])
    if sha256_file(source_path / "app.js") != result["preparation"][
        "source_app_sha256"
    ]:
        raise ValueError(f"Baseline source changed after execution for {cwe}.")
    return binding, result


def verify_candidate_group(
    project_root: Path,
    cwe: str,
    expected_ids: list[str],
    baseline_binding: dict[str, str],
    bound_binding: dict[str, str] | None = None,
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    if bound_binding is None:
        summary_path = latest_completed_candidate_group(project_root, cwe)
    else:
        summary_path, _ = _verify_bound_run(
            project_root, bound_binding, cwe, "candidates", "summary.json"
        )
    group = load_json(summary_path)
    if (
        group.get("protocol_id") != "supplemental-v1"
        or group.get("cwe_case") != cwe
        or group.get("status") != "completed"
        or group.get("candidate_count") != 5
        or group.get("run_id") != summary_path.parent.name
    ):
        raise ValueError(f"Candidate group identity mismatch for {cwe}.")
    if group.get("baseline_gate") != baseline_binding:
        raise ValueError(f"Candidate group uses a different baseline for {cwe}.")

    results = []
    expected_attempts = [1, 2, 3, 4, 5]
    group_attempts = [row.get("attempt") for row in group.get("candidates", [])]
    if group_attempts != expected_attempts:
        raise ValueError(f"Candidate attempt order differs for {cwe}.")

    for attempt in expected_attempts:
        result_path = summary_path.parent / f"attempt-{attempt:02d}/result.json"
        result = load_json(result_path)
        if result.get("status") != "candidate_evaluated":
            raise ValueError(f"Candidate execution incomplete: {result_path}")
        if result.get("attempt") != attempt:
            raise ValueError(f"Candidate attempt mismatch: {result_path}")
        if (
            result.get("protocol_id") != "supplemental-v1"
            or result.get("cwe_case") != cwe
        ):
            raise ValueError(f"Candidate identity mismatch: {result_path}")
        if result.get("baseline_gate") != baseline_binding:
            raise ValueError(f"Candidate baseline binding mismatch: {result_path}")
        ids = [case.get("test_id") for case in result.get("cases", [])]
        if ids != expected_ids:
            raise ValueError(f"Candidate test IDs differ: {result_path}")

        recomputed = summarize_candidate_cases(result["cases"])
        if result.get("summary") != recomputed:
            raise ValueError(f"Candidate summary does not recompute: {result_path}")
        source_path = Path(result["preparation"]["source_app"])
        if sha256_file(source_path / "app.js") != result["preparation"][
            "source_app_sha256"
        ]:
            raise ValueError(f"Candidate source changed after run: {result_path}")
        results.append(
            {
                "attempt": attempt,
                "path": _relative(project_root, result_path),
                "sha256": sha256_file(result_path),
                "summary": recomputed,
                "nonpassing_tests": [
                    {
                        "test_id": case["test_id"],
                        "category": case["category"],
                        "status": case[
                            "candidate_expectation_evaluation"
                        ]["status"],
                    }
                    for case in result["cases"]
                    if case["candidate_expectation_evaluation"]["status"]
                    != "pass"
                ],
            }
        )

    expected_group_rows = [
        {"attempt": row["attempt"], "status": "candidate_evaluated", **row["summary"]}
        for row in results
    ]
    if group.get("candidates") != expected_group_rows:
        raise ValueError(f"Candidate group rows do not recompute for {cwe}.")

    binding = {
        "path": _relative(project_root, summary_path),
        "sha256": sha256_file(summary_path),
        "run_id": group["run_id"],
    }
    return binding, results


def find_superseded_runs(
    project_root: Path,
    bound_entries: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    runs = project_root.resolve() / "data/supplemental/v1/runs"
    superseded = []
    paths = (
        sorted(runs.glob("*-baseline-*/result.json"))
        if bound_entries is None
        else [
            resolve_project_path(project_root, entry["path"])
            for entry in bound_entries
        ]
    )
    for path in paths:
        if (
            path.parent.parent != runs
            or "-baseline-" not in path.parent.name
            or path.name != "result.json"
        ):
            raise ValueError(f"Invalid superseded baseline path: {path}")
        result = load_json(path)
        if result.get("status") == "baseline_characterized":
            if bound_entries is not None:
                raise ValueError(f"Bound superseded baseline is successful: {path}")
            continue
        investigation = path.parent / "investigation.json"
        entry: dict[str, Any] = {
            "path": _relative(project_root, path),
            "sha256": sha256_file(path),
            "status": result.get("status"),
            "used_as_candidate_gate": False,
        }
        if investigation.is_file():
            entry["investigation"] = {
                "path": _relative(project_root, investigation),
                "sha256": sha256_file(investigation),
            }
        superseded.append(entry)
    if bound_entries is not None and superseded != bound_entries:
        raise ValueError("Bound superseded baseline evidence has changed.")
    return superseded


def build_supplemental_report(
    project_root: Path,
    bound_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = project_root.resolve()
    definition = verify_definition(root)
    manifest = load_json(resolve_project_path(root, str(DEFAULT_CASES)))
    bound_cwes = None if bound_report is None else bound_report["cwes"]
    if bound_cwes is not None and [
        row.get("cwe_case") for row in bound_cwes
    ] != list(CWE_ORDER):
        raise ValueError("Bound supplemental report has different CWE entries.")
    aggregate = {
        "security": _empty_counts(),
        "behavioral_parity": _empty_counts(),
        "robustness_contract": _empty_counts(),
    }
    cwe_results = []
    evidence_times = []

    for index, cwe in enumerate(CWE_ORDER):
        bound_row = None if bound_cwes is None else bound_cwes[index]
        expected_ids = [
            test["id"] for test in manifest["cwes"][cwe]["tests"]
        ]
        baseline_binding, baseline = verify_baseline_result(
            root,
            cwe,
            expected_ids,
            None if bound_row is None else bound_row["baseline"],
        )
        group_binding, candidates = verify_candidate_group(
            root,
            cwe,
            expected_ids,
            baseline_binding,
            None if bound_row is None else bound_row["candidate_group"],
        )
        for candidate in candidates:
            for category, counts in candidate["summary"]["by_category"].items():
                _add_counts(aggregate[category], counts)
        evidence_times.append(baseline["finished_at"])
        group = load_json(resolve_project_path(root, group_binding["path"]))
        evidence_times.append(group["finished_at"])
        cwe_results.append(
            {
                "cwe_case": cwe,
                "baseline": {
                    **baseline_binding,
                    "summary": baseline["summary"],
                },
                "candidate_group": group_binding,
                "candidates": candidates,
            }
        )

    total = _empty_counts()
    for counts in aggregate.values():
        _add_counts(total, counts)

    return {
        "schema_version": "0.1",
        "project": "FixProof",
        "artifact_type": "verified_supplemental_report",
        "protocol_id": "supplemental-v1",
        "evidence_verified": True,
        "verification_mode": "recorded_supplemental_evidence_no_model_or_sast_calls",
        "evidence_cutoff": max(evidence_times),
        "definition": definition,
        "baseline_count": 3,
        "saved_candidate_count": 15,
        "candidate_case_observations": total,
        "candidate_observations_by_category": aggregate,
        "cwes": cwe_results,
        "superseded_or_invalid_runs": find_superseded_runs(
            root,
            None if bound_report is None else bound_report["superseded_or_invalid_runs"],
        ),
        "follow_up_review_targets": [
            "primary-v1-xss-initial-04",
            "primary-v1-xss-initial-05",
            "primary-v1-path-traversal-initial-01",
        ],
        "limitations": [
            "The Windows symlink/junction fixture was unavailable, so PATH-S06 is inconclusive for the baseline and all five traversal candidates.",
            "One fixture per CWE and repeated saved candidates do not form a representative application corpus.",
            "Supplemental passing outcomes do not establish application-wide security or deployment approval.",
            "Robustness contracts are supplemental requirements and are not retroactive primary-v1 functional failures.",
        ],
        "automatic_acceptance": False,
        "human_follow_up_required": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build or verify the recorded FixProof supplemental report."
    )
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/supplemental/v1/supplemental-report.json"),
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    root = args.project_root.resolve()
    output = (
        args.output.resolve()
        if args.output.is_absolute()
        else (root / args.output).resolve()
    )
    resolve_project_path(root, _relative(root, output))
    if args.check:
        if not output.is_file():
            raise FileNotFoundError(f"Supplemental report not found: {output}")
        stored = load_json(output)
        report = build_supplemental_report(root, bound_report=stored)
        if stored != report:
            raise ValueError("Stored supplemental report is stale or inconsistent.")
        print("Supplemental evidence verified: 3 baselines, 15 saved candidates")
        print("Saved run bindings verified; later reruns remain separate.")
    else:
        report = build_supplemental_report(root)
        write_json(output, report)
        print(f"Supplemental report: {_relative(root, output)}")


if __name__ == "__main__":
    main()
