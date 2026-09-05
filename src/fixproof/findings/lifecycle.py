"""Append verified-scan snapshots to a local four-state finding history.

Matching is limited to relative file + CWE + Express scope. Ambiguous keys,
incomplete scans, changed coverage, and changed ruleset labels are rejected.
This post-collection feature does not alter the frozen primary comparator.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from fixproof.evaluation.adjudication import _resolve_project_file
from fixproof.scanners.semgrep_parser import normalize_result
from fixproof.validation.validation_runner import get_scope_signature


class LifecycleError(ValueError):
    pass


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise LifecycleError(message)


def snapshot_from_scan(project_root: Path, source_root: Path, raw_scan: Path,
                       version: str, ruleset_id: str) -> dict:
    project_root, source_root, raw_scan = project_root.resolve(), source_root.resolve(), raw_scan.resolve()
    _require(source_root.is_relative_to(project_root), "Source root must be inside the project")
    _require(raw_scan.is_relative_to(project_root), "Scan must be inside the project")
    raw = json.loads(raw_scan.read_text(encoding="utf-8"))
    _require("results" in raw and not raw.get("errors"), "A complete, error-free scan is required")
    files = {}
    for scanned in raw.get("paths", {}).get("scanned", []):
        path = _resolve_project_file(project_root, scanned, "scanned source")
        _require(path.is_relative_to(source_root), "Scanned file lies outside source scope")
        relative = path.relative_to(source_root).as_posix()
        files[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    _require(bool(files), "Scan must declare at least one scanned source file")
    findings = []
    for result in raw["results"]:
        path = _resolve_project_file(project_root, result["path"], "finding source")
        _require(path.is_relative_to(source_root), "Finding lies outside source scope")
        relative = path.relative_to(source_root).as_posix()
        _require(relative in files, "Finding is absent from scanned-file coverage")
        local = dict(result, path=str(path))
        finding = normalize_result(local, source_root)
        _require(finding.get("cwe") is not None, "A CWE is required for lifecycle matching")
        scope = get_scope_signature(path, finding)
        identity = {"file": relative, "cwe": finding["cwe"], "scope": scope}
        # Multiple scanner rules for the same location are corroborating evidence.
        existing = next((item for item in findings if item["identity"] == identity), None)
        location = [finding["start_line"], finding["end_line"]]
        if existing:
            _require(existing["start_line"] == location[0],
                     "Ambiguous same-CWE findings in one scope; cannot track automatically")
            existing["rule_ids"] = sorted(set(existing["rule_ids"] + [finding["rule_id"]]))
        else:
            findings.append({"identity": identity, "start_line": location[0],
                             "rule_ids": [finding["rule_id"]]})
    return {"version": version, "ruleset_id": ruleset_id,
            "scanner_version": raw.get("version"), "scan_complete": True,
            "coverage": sorted(files), "source_hashes": files,
            "scan_binding": {"path": raw_scan.relative_to(project_root).as_posix(),
                             "sha256": hashlib.sha256(raw_scan.read_bytes()).hexdigest()},
            "findings": sorted(findings, key=lambda item: digest(item["identity"]))}


def _append(history: dict, snapshot: dict) -> dict:
    for field in ("version", "ruleset_id", "scanner_version"):
        _require(isinstance(snapshot.get(field), str) and bool(snapshot[field].strip()), f"Missing {field}")
    _require(snapshot.get("scan_complete") is True, "Incomplete scans cannot resolve findings")
    coverage = snapshot.get("coverage", [])
    _require(isinstance(coverage, list) and bool(coverage) and coverage == sorted(set(coverage)), "Invalid scan coverage")
    previous = history["snapshots"][-1] if history["snapshots"] else None
    if previous:
        for field in ("coverage", "ruleset_id", "scanner_version"):
            _require(previous["snapshot"][field] == snapshot[field], f"Changed {field}; start a separate comparable history")
    seen = {}
    for finding in snapshot["findings"]:
        identity = finding["identity"]
        _require(set(identity) == {"file", "cwe", "scope"}, "Invalid finding identity")
        _require(identity["file"] in coverage, "Finding outside coverage")
        _require(all(isinstance(value, str) and value for value in identity.values()), "Empty finding identity")
        key = digest(identity)
        _require(key not in seen, "Ambiguous duplicate lifecycle identity")
        seen[key] = finding
    state = json.loads(json.dumps(history["findings"]))
    events = []
    for key, finding in sorted(seen.items()):
        old = state.get(key)
        status = "new" if old is None else "reopened" if old["status"] == "resolved" else "persistent"
        state[key] = {"identity": finding["identity"], "status": status,
                      "first_seen": old["first_seen"] if old else snapshot["version"],
                      "last_seen": snapshot["version"], "resolved_in": None,
                      "reopen_count": (old["reopen_count"] if old else 0) + int(status == "reopened")}
        events.append({"finding_id": key, "status": status})
    for key, old in sorted(state.items()):
        if key not in seen and old["status"] != "resolved":
            old["status"] = "resolved"
            old["resolved_in"] = snapshot["version"]
            events.append({"finding_id": key, "status": "resolved"})
    entry = {"snapshot": snapshot, "previous_sha256": previous["sha256"] if previous else None,
             "events": events}
    entry["sha256"] = digest(entry)
    return {"schema_version": "0.1", "project": "FixProof", "artifact_type": "finding_lifecycle",
            "snapshots": history["snapshots"] + [entry], "findings": state}


def empty_history() -> dict:
    return {"schema_version": "0.1", "project": "FixProof", "artifact_type": "finding_lifecycle",
            "snapshots": [], "findings": {}}


def validate_history(history: dict) -> None:
    rebuilt = empty_history()
    versions = set()
    for entry in history["snapshots"]:
        version = entry["snapshot"]["version"]
        _require(version not in versions, "Duplicate version in stored history")
        versions.add(version)
        rebuilt = _append(rebuilt, entry["snapshot"])
    _require(rebuilt == history, "History chain or derived finding state is inconsistent")


def append_snapshot(history: dict, snapshot: dict) -> dict:
    validate_history(history)
    for entry in history["snapshots"]:
        if entry["snapshot"]["version"] == snapshot["version"]:
            _require(entry["snapshot"] == snapshot, "Version already exists with different evidence")
            return history
    return _append(history, snapshot)


def record_snapshot(path: Path, snapshot: dict) -> dict:
    lock = path.with_suffix(path.suffix + ".lock")
    # Only remove the lock when this invocation acquired it.
    acquired = False
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        handle = lock.open("x", encoding="utf-8")
        acquired = True
        handle.close()
        history = json.loads(path.read_text(encoding="utf-8")) if path.exists() else empty_history()
        updated = append_snapshot(history, snapshot)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(updated, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
        return updated
    finally:
        if acquired:
            lock.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--raw-scan", type=Path)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--version")
    parser.add_argument("--ruleset-id", help="Explicit identifier of comparable scanner rules; do not use a changed auto rulepack under the same ID")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if args.check:
            history = json.loads(args.history.read_text(encoding="utf-8"))
            validate_history(history)
        else:
            if not all((args.raw_scan, args.source_root, args.version, args.ruleset_id)):
                parser.error("recording requires --raw-scan, --source-root, --version, and --ruleset-id")
            snapshot = snapshot_from_scan(args.project_root, args.source_root, args.raw_scan, args.version, args.ruleset_id)
            history = record_snapshot(args.history, snapshot)
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(1, f"Lifecycle verification failed: {error}\n")
    print(f"Verified snapshots: {len(history['snapshots'])}")
    print(f"Current finding states: {dict(Counter(f['status'] for f in history['findings'].values()))}")


if __name__ == "__main__":
    main()
