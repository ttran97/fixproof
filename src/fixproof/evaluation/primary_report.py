"""Verify and report the completed primary-v1 study without rerunning generation.

This post-collection adapter leaves the frozen collector and its evidence intact.
It deliberately fails on incomplete collections instead of presenting partial data
as a completed study. Runtime observations are checked for consistency, not rerun.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

from fixproof.evaluation.adjudication import (
    build_pending_packet, _resolve_project_file, _sha256_normalized_text,
)
from fixproof.evaluation.report_builder import (
    ReportDataError, _artifact_record, _build_attempt_row, load_json,
)
from fixproof.primary_trials import (
    build_collection_state, build_schedule, prepare_case, validate_frozen_inputs,
)
from fixproof.scanners.semgrep_parser import normalize_result, make_finding_id
from fixproof.findings.finding_correlator import correlate_findings
from fixproof.validation.validation_runner import compare_findings
from fixproof.validation.decision_engine import classify_outcome, determine_disposition

STUDY = Path("data/primary_trials/v1")
REVIEWS = Path("data/primary_reviews/v1")
REPORT = Path("data/evaluation/primary-report.json")
MARKDOWN = Path("docs/primary-results.md")
NAMES = {"xss": "Reflected XSS", "sqli": "SQL injection", "path-traversal": "Path traversal"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReportDataError(message)


def project_file(root: Path, value: str) -> Path:
    path = (root / value).resolve()
    require(path.is_relative_to(root.resolve()), f"Path escapes project: {value}")
    require(path.is_file(), f"Missing evidence: {value}")
    return path


def check_binding(root: Path, record: dict[str, str]) -> Path:
    path = project_file(root, record["path"])
    require(hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"],
            f"Changed evidence: {record['path']}")
    return path


def _portable_findings(payload: dict, filename: str) -> dict:
    result = copy.deepcopy(payload)
    for finding in result["findings"]:
        finding["file"] = filename
    return result


def _portable_comparison(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: Path(v.replace('\\', '/')).name if k == "file" else
                _portable_comparison(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_portable_comparison(v) for v in value]
    return value


def _portable_metadata(root: Path, value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _resolve_project_file(root, item, key).relative_to(root).as_posix()
                if key == "resolved_path" and isinstance(item, str) else
                _portable_metadata(root, item) for key, item in value.items()}
    if isinstance(value, list):
        return [_portable_metadata(root, item) for item in value]
    return value


def verify_candidate_scan(root: Path, folder: Path, candidate: Path, temporary: Path) -> dict:
    """Reconstruct scanner normalization using only the active candidate source."""
    raw = load_json(folder / "sast/candidate-semgrep-raw.json")
    normalized = load_json(folder / "sast/candidate-normalized.json")
    require(raw.get("version") == "1.136.0", "Unexpected primary scanner version")
    require(not raw.get("errors"), "Candidate scan contains scanner errors")
    rebuilt = []
    for result in raw.get("results", []):
        original = result["path"]
        resolved = _resolve_project_file(root, original, "candidate scan path")
        require(resolved == candidate, "Candidate scan references a different source")
        local = copy.deepcopy(result)
        local["path"] = str(candidate)
        finding = normalize_result(local, candidate.parent)
        finding["file"] = original
        finding["finding_id"] = make_finding_id(
            finding["rule_id"], original, finding["start_line"], finding["end_line"]
        )
        rebuilt.append(finding)
    require(_portable_metadata(root, rebuilt) == _portable_metadata(root, normalized["findings"]),
            "Candidate normalization does not match raw scan/source")
    require(normalized["scan"]["finding_count"] == len(rebuilt), "Wrong candidate finding count")
    normalized_file = temporary / "normalized.json"
    normalized_file.write_text(json.dumps(normalized), encoding="utf-8")
    correlated = correlate_findings(normalized_file, temporary / "correlated.json")
    require(correlated == load_json(folder / "sast/candidate-correlated.json"),
            "Candidate correlation does not match normalized findings")
    return correlated


def build_primary_report(root: Path) -> dict[str, Any]:
    root = root.resolve()
    frozen = validate_frozen_inputs(root)
    schedule = build_schedule(frozen)
    manifest_path = root / STUDY / "primary-experiment-manifest.json"
    manifest = load_json(manifest_path)
    require(manifest["attempts"] == schedule, "Primary schedule differs from frozen design")
    require(manifest["manifest_sha256"] == frozen["manifest_sha256"], "Benchmark manifest binding differs")
    require(manifest["model"] == frozen["model"], "Primary model differs from frozen design")
    for path, digest in manifest["implementation_files"].items():
        check_binding(root, {"path": path, "sha256": digest})
    rows = []
    bindings = {}
    candidate_hashes: dict[str, set[str]] = {case: set() for case in NAMES}
    response_ids = set()
    with tempfile.TemporaryDirectory(prefix="fixproof-primary-report-") as temp:
        temporary = Path(temp)
        for case in frozen["manifest"]["cases"]:
            recorded = manifest["preparations"][case["case_id"]]
            rebuilt = prepare_case(root, frozen, case, temporary / case["case_id"])
            for name in ("canonical_id", "prompt_sha256", "baseline_raw_sha256", "target_rule_ids", "target_rule_origin"):
                require(recorded[name] == rebuilt[name], f"Preparation mismatch: {case['case_id']} {name}")
            for name in ("baseline_correlated", "contexts", "prompts"):
                saved = project_file(root, recorded[name])
                require(_portable_metadata(root, load_json(saved)) == _portable_metadata(root, load_json(Path(rebuilt[name]))),
                        f"Reconstructed preparation differs: {recorded[name]}")
                bindings[saved.relative_to(root).as_posix()] = _artifact_record(root, saved)
        for index, scheduled in enumerate(schedule):
            case_id, attempt = scheduled["case_id"], scheduled["attempt"]
            folder = root / STUDY / "cases" / case_id / f"attempt-{attempt:02d}"
            record = load_json(folder / "attempt.json")
            require(record.get("status") == "completed" and record.get("terminal") is True,
                    f"Primary collection is incomplete: {scheduled['trial_id']}")
            for key, value in scheduled.items():
                if key != "status":
                    require(record.get(key) == value, f"Attempt identity mismatch: {scheduled['trial_id']} {key}")
            prep = manifest["preparations"][case_id]
            require(record["prompt_sha256"] == prep["prompt_sha256"], "Attempt prompt binding differs")
            require(record["manifest_sha256"] == frozen["manifest_sha256"], "Attempt benchmark binding differs")
            require(record["model"] == frozen["model"], "Attempt model differs")
            require(set(record["artifacts"]) == {"remediation", "workspace", "patch", "preliminary", "security", "functional", "decision"},
                    "Expected a complete seven-artifact candidate evidence chain")
            paths = {name: check_binding(root, binding) for name, binding in record["artifacts"].items()}
            for path in paths.values():
                require(path.is_relative_to(folder), "Attempt references another attempt's evidence")
            workspace = load_json(paths["workspace"])["patch_workspace"]
            require(workspace["original_modified"] is False, "Baseline was modified")
            for field, digest in (("original_source", "original_source_sha256"),
                                  ("workspace_source", "candidate_source_sha256"),
                                  ("patch_file", "patch_sha256")):
                source = _resolve_project_file(root, workspace[field], field)
                require(_sha256_normalized_text(source) == workspace["hashes"][digest],
                        f"Workspace content changed: {record['trial_id']} {field}")
                bindings[source.relative_to(root).as_posix()] = _artifact_record(root, source)
            baseline = root / "benchmarks/primary/v1" / case_id / "app.js"
            require(_resolve_project_file(root, workspace["original_source"], "baseline") == baseline,
                    "Workspace references a different baseline")
            candidate = _resolve_project_file(root, workspace["workspace_source"], "candidate")
            require(candidate.is_relative_to(folder / "workspace"), "Candidate is outside its attempt workspace")
            correlated = verify_candidate_scan(root, folder, candidate, temporary)
            comparison = compare_findings(
                _portable_findings(load_json(root / prep["baseline_correlated"]), baseline.name),
                _portable_findings(correlated, candidate.name), baseline.parent, candidate.parent,
                record["canonical_id"],
            )
            preliminary = load_json(paths["preliminary"])["validation"]
            require(comparison == _portable_comparison(preliminary["comparison"]), "Recorded finding comparison differs")
            entry = {**scheduled, "case": NAMES[case_id], "canonical_id": record["canonical_id"],
                     "candidate_origin": "ai_generated", "metric_scope": "primary_ai_attempt_metrics",
                     "artifacts": {name: binding["path"] for name, binding in record["artifacts"].items() if name != "patch"}}
            entry["artifacts"]["baseline_correlated"] = prep["baseline_correlated"]
            review_folder = root / REVIEWS / record["trial_id"]
            for kind in ("packet", "result"):
                path = review_folder / f"{kind}.json"
                if path.exists():
                    entry["artifacts"][f"adjudication_{kind}"] = path.relative_to(root).as_posix()
            row = _build_attempt_row(root, entry, index)
            require(row["model"] == frozen["model"], "Saved response model differs from frozen design")
            decision = load_json(paths["decision"])["decision"]
            security = load_json(paths["security"])["security_validation"]
            functional = load_json(paths["functional"])["functional_validation"]
            case = next(c for c in frozen["manifest"]["cases"] if c["case_id"] == case_id)
            for kind, results in (("security", security), ("functional", functional)):
                require([t["test"] for t in results["tests"]] == case["tests"][kind]["names"],
                        f"Frozen {kind} tests changed: {record['trial_id']}")
            if case_id == "xss":
                for test in security["tests"]:
                    browser = test["evaluation"].get("browser", {})
                    require(browser.get("status") in ("executed", "not_executed", "inconclusive"), "Missing browser observation")
                    if test["evaluation"]["status"] == "pass":
                        require(browser.get("status") == "not_executed" and browser.get("executed") is False,
                                "Passing XSS test lacks non-execution evidence")
            arguments = dict(syntax_status=preliminary["syntax"]["status"],
                             target_sast_status=comparison["target"]["status"],
                             new_findings=comparison["summary"]["new"],
                             security_status=security["status"], functional_status=functional["status"])
            policy = determine_disposition(**arguments)
            for key in ("disposition", "reason_codes", "retry_allowed", "eligible_for_human_approval", "recommended_action"):
                require(decision[key] == policy[key], f"Policy mismatch: {record['trial_id']} {key}")
            require(decision["classification"] == classify_outcome(**arguments), "Classification mismatch")
            for key in ("evidence", "evaluation_labels", "disposition", "classification"):
                require(record[key] == decision[key], f"Attempt summary differs from decision: {key}")
            require(record["sast_only_interpretation"] == frozen["plan"]["comparison"]["sast_only_mapping"][arguments["target_sast_status"]],
                    "SAST-only interpretation mismatch")
            require(row["response_id"] == record["response_id"] == workspace["response_id"], "Response identity mismatch")
            require(row["response_id"] and row["response_id"] not in response_ids, "Missing or reused model response ID")
            response_ids.add(row["response_id"])
            candidate_hashes[case_id].add(workspace["hashes"]["candidate_source_sha256"])
            row.update(trial_id=record["trial_id"], sast_only=record["sast_only_interpretation"])
            row["review_material"] = {
                "baseline_source": baseline.read_text(encoding="utf-8"),
                "candidate_source": candidate.read_text(encoding="utf-8"),
                "patch": paths["patch"].read_text(encoding="utf-8"),
                "target_rule_ids": prep["target_rule_ids"],
                "candidate_findings": load_json(folder / "sast/candidate-normalized.json")["findings"],
                "security_tests": security["tests"], "functional_tests": functional["tests"],
            }
            row["artifacts"]["patch"] = record["artifacts"]["patch"]
            rows.append(row)
            for path in [folder / "attempt.json", *paths.values(), *sorted((folder / "sast").glob("*.json"))]:
                bindings[path.relative_to(root).as_posix()] = _artifact_record(root, path)
    state = build_collection_state(root / STUDY, schedule)
    saved_state = load_json(root / STUDY / "collection-state.json")
    require({k: v for k, v in state.items() if k != "updated_at"} ==
            {k: v for k, v in saved_state.items() if k != "updated_at"}, "Collection summary is stale")
    counts = Counter(row["adjudication"]["status"] for row in rows if row["adjudication"]["required"])
    return {"schema_version": "0.1", "project": "FixProof", "artifact_type": "verified_primary_report",
            "suite_id": "primary-v1", "evidence_verified": True,
            "verification_mode": "recorded_evidence_no_scanner_model_or_runtime_calls",
            "manifest": _artifact_record(root, manifest_path), "attempt_count": len(schedule),
            "metrics": state["primary_metrics"], "experiment_matrix": rows,
            "adjudication_summary": {"required": sum(counts.values()), "completed": counts["completed"],
                                     "pending": counts["pending"], "missing_packet": counts["missing_packet"]},
            "unique_candidate_sources": {case: len(hashes) for case, hashes in candidate_hashes.items()},
            "evidence_bindings": list(bindings.values()),
            "limitations": ["One application per CWE; repeated prompts are not independent applications.",
                            "Passing targeted tests is not proof of application-wide security.",
                            "Default Semgrep auto rule definitions were not fully archived.",
                            "Pilot attempts, retry, and non-AI control are excluded from primary rates.",
                            "Evidence verification does not perform or attest human review."]}


def render_primary_markdown(report: dict) -> str:
    lines = ["# FixProof primary-v1 results", "", "Generated from verified recorded evidence; no model or runtime tests are rerun.", "",
             "| Trial | Target SAST | Security | Functional | Decision | Human review |",
             "|---|---|---|---|---|---|"]
    for row in report["experiment_matrix"]:
        e = row["evidence"]
        lines.append(f"| {row['trial_id']} | {e['target_sast']} | {e['security']['passed']}/{e['security']['total']} | "
                     f"{e['functional']['passed']}/{e['functional']['total']} | {row['decision']} | {row['adjudication']['status']} |")
    lines += ["", "## Primary metrics", "", "All rates use the 15 scheduled initial attempts; pilot and control evidence are separate.", ""]
    for name, metric in report["metrics"].items():
        if isinstance(metric, dict) and "denominator" in metric:
            lines.append(f"- {name}: {metric['count']}/{metric['denominator']} ({100 * metric['rate']:.1f}%).")
    review = report["adjudication_summary"]
    lines += ["", f"Conflict reviews completed: **{review['completed']}/{review['required']}**. "
              "Ready for human review does not mean human approval.", "",
              f"Distinct candidate sources per case: {report['unique_candidate_sources']}.", "",
              f"Observed primary SAST false successes: {report['metrics']['sast_false_success']['count']}. "
              "Pilot and non-AI control outcomes must be discussed separately.", "",
              "Primary retry improvement is not applicable when no initial primary candidate is rejected. "
              "This report contains initial attempts only.", "", "## Limits", ""]
    lines += [f"- {limit}" for limit in report["limitations"]]
    return "\n".join(lines) + "\n"


def write_primary_report(root: Path, *, initialize_reviews: bool = False) -> dict:
    root = root.resolve()
    report = build_primary_report(root)
    if initialize_reviews:
        for row in report["experiment_matrix"]:
            if not row["adjudication"]["required"]:
                continue
            path = root / REVIEWS / row["trial_id"] / "packet.json"
            payload = build_pending_packet(root, row)
            if path.exists():
                require(load_json(path) == payload, "Refusing to replace a stale review packet")
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        report = build_primary_report(root)
    (root / REPORT).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (root / MARKDOWN).write_text(render_primary_markdown(report), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--init-reviews", action="store_true", help="Create pending evidence packets; never create human verdicts")
    parser.add_argument("--check", action="store_true", help="Verify evidence without writing derived reports")
    args = parser.parse_args()
    if args.check and args.init_reviews:
        parser.error("--check cannot be combined with --init-reviews")
    try:
        report = build_primary_report(args.project_root) if args.check else write_primary_report(args.project_root, initialize_reviews=args.init_reviews)
        if args.check:
            require(load_json(args.project_root / REPORT) == report,
                    "Derived primary JSON is stale; regenerate the primary report")
            require((args.project_root / MARKDOWN).read_text(encoding="utf-8") == render_primary_markdown(report),
                    "Derived primary Markdown is stale; regenerate the primary report")
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(1, f"Primary evidence verification failed: {error}\n")
    review = report["adjudication_summary"]
    print(f"Primary evidence verified: {report['attempt_count']}/15 initial attempts")
    print(f"Human conflict reviews: {review['completed']}/{review['required']} complete; "
          f"{review['pending']} pending; {review['missing_packet']} packets missing")
    print("Evidence verification is not final-submission approval.")


if __name__ == "__main__":
    main()
