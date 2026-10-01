"""Build the student-facing FixProof case-evidence workbook and public data.

The export is derived only from verified, recorded evidence. It does not run a
model, scanner, candidate application, or test case. Primary-v1,
supplemental-v1, and the PATH-S06 extension remain distinct evidence layers.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qsl, quote_plus, urlencode, urlsplit
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = Path(__file__).resolve().parent
CSV_DIR = OUTPUT_DIR / "student-evidence-csv"
PUBLIC = ROOT / "fixproof-public"

WORKBOOK_NAME = "FixProof-15-candidate-test-evidence.xlsx"
WORKBOOK = OUTPUT_DIR / WORKBOOK_NAME
PUBLIC_WORKBOOK = PUBLIC / WORKBOOK_NAME
PUBLIC_JSON = PUBLIC / "data" / "student-test-evidence.json"
VALIDATION = OUTPUT_DIR / "FixProof-student-evidence-validation.json"

PRIMARY_REPORT = ROOT / "data" / "evaluation" / "primary-report.json"
SUPPLEMENTAL_REPORT = (
    ROOT / "data" / "supplemental" / "v1" / "supplemental-report.json"
)
EXTENSION_CASE = ROOT / "tests" / "extensions" / "path_s06" / "v1" / "case.json"
EXTENSION_RUN_ID = "20260930T180925912688Z-path-s06-v1"
EXTENSION_SUMMARY = (
    ROOT
    / "data"
    / "extensions"
    / "path-s06-v1"
    / "runs"
    / EXTENSION_RUN_ID
    / "summary.json"
)

CASE_ORDER = {"xss": 0, "sqli": 1, "path-traversal": 2}
CASE_LABELS = {
    "xss": "Reflected XSS",
    "sqli": "SQL injection",
    "path-traversal": "Path traversal",
}
SHORT_LABELS = {
    "xss": "XSS",
    "sqli": "SQLi",
    "path-traversal": "Traversal",
}

DETAIL_HEADERS = [
    "Candidate",
    "CWE",
    "Evidence layer",
    "Category",
    "Case/Test ID",
    "Input/Payload",
    "HTTP method",
    "Effective request(s)",
    "Recorded observation count",
    "Expected result/contract",
    "Observed HTTP status(es)",
    "Observed response/output",
    "Browser/secondary observation",
    "Result",
    "Evaluation reason",
    "Source evidence",
]

SUMMARY_HEADERS = [
    "Candidate",
    "Trial ID",
    "CWE",
    "Target SAST",
    "Primary security",
    "Primary functional",
    "Automated state",
    "Original human",
    "Supplemental security P/F/I",
    "Supplemental parity P/F/I",
    "Supplemental robustness P/F/I",
    "Supplemental later human",
    "PATH-S06 extension P/F/I",
    "PATH-S06 later human",
]

COUNT_HEADERS = [
    "Evidence layer",
    "Unit/category",
    "Denominator",
    "Pass/resolved",
    "Fail/persistent",
    "Inconclusive",
    "Meaning",
]

HUMAN_HEADERS = [
    "Candidate",
    "Evidence layer",
    "Reviewed on",
    "Verdict",
    "Rationale",
    "Relationship/notes",
    "Source evidence",
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def candidate_label(case_id: str, attempt: int) -> str:
    return f"{SHORT_LABELS[case_id]} {attempt:02d}"


def json_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple, bool)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value)


def compact_body(value: Any) -> str:
    text = json_value(value)
    return text.replace("\r\n", "\n").replace("\r", "\n")


def status_text(status: Any) -> str:
    return str(status or "").strip().upper()


def pfi(raw: dict[str, Any] | None) -> str:
    raw = raw or {}
    return (
        f"{int(raw.get('pass', 0))}/"
        f"{int(raw.get('fail', 0))}/"
        f"{int(raw.get('inconclusive', 0))}"
    )


def safe_query_value(value: str) -> str:
    """Remove local-user path details while retaining the payload class."""

    if re.match(r"^[A-Za-z]:[\\/]", value):
        return "<generated Windows absolute path>"
    if re.match(r"^/[A-Za-z]:/", value):
        return "<generated POSIX absolute path>"
    return value


def normalized_request_target(url: str) -> str:
    """Return a stable relative request target without a transient host/port."""

    parsed = urlsplit(url)
    pairs = [
        (name, safe_query_value(value))
        for name, value in parse_qsl(parsed.query, keep_blank_values=True)
    ]
    query = urlencode(pairs, doseq=True)
    return parsed.path + (f"?{query}" if query else "")


def derived_request(route: str, parameter: str, value: str) -> str:
    return f"{route}?{quote_plus(parameter)}={quote_plus(value)}"


def expected_fields(evaluation: dict[str, Any]) -> str:
    fields: list[str] = []
    for key, value in evaluation.items():
        if key.startswith("expected_") or key == "forbidden_body":
            fields.append(f"{key}={json_value(value)}")
    return "\n".join(fields)


def browser_summary(browser: dict[str, Any] | None) -> str:
    if not browser:
        return ""
    parts: list[str] = []
    for key in ("status", "executed", "http_status", "h1_count"):
        if key in browser:
            parts.append(f"{key}={json_value(browser[key])}")
    for key in ("dialogs", "h1_texts", "active_element_counts", "page_errors"):
        if key in browser and browser[key] not in (None, [], {}):
            parts.append(f"{key}={json_value(browser[key])}")
    return "; ".join(parts)


def flatten_supplemental_observations(case: dict[str, Any]) -> list[dict[str, Any]]:
    evidence = case.get("evidence", {})
    observations = list(evidence.get("observations", []))
    if observations:
        return observations

    references = evidence.get("references", [])
    flattened: list[dict[str, Any]] = []
    for index, referenced in enumerate(evidence.get("referenced_results", [])):
        reference = references[index] if index < len(references) else f"reference-{index + 1}"
        for observation in referenced.get("observations", []):
            copied = dict(observation)
            copied["label"] = f"{reference}:{observation.get('label', 'request')}"
            flattened.append(copied)
    return flattened


def primary_rows(primary: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for candidate in sorted(
        primary["experiment_matrix"],
        key=lambda row: (CASE_ORDER[str(row["case_id"])], int(row["attempt"])),
    ):
        case_id = str(candidate["case_id"])
        attempt = int(candidate["attempt"])
        label = candidate_label(case_id, attempt)
        case_dir = (
            ROOT
            / "data"
            / "primary_trials"
            / "v1"
            / "cases"
            / case_id
            / f"attempt-{attempt:02d}"
        )
        for filename, root_key, category in (
            ("security.json", "security_validation", "security"),
            ("functional.json", "functional_validation", "functional"),
        ):
            source = case_dir / filename
            document = load_json(source)[root_key]
            target = document["target"]
            for test in document["tests"]:
                value = str(test.get("payload", test.get("input", "")))
                evaluation = test.get("evaluation", {})
                http = test.get("http", {})
                browser = evaluation.get("browser")
                rows.append(
                    {
                        "Candidate": label,
                        "CWE": str(document["cwe"]),
                        "Evidence layer": "primary-v1",
                        "Category": category,
                        "Case/Test ID": str(test["test"]),
                        "Input/Payload": value,
                        "HTTP method": "GET",
                        "Effective request(s)": derived_request(
                            str(target["route"]),
                            str(target["query_parameter"]),
                            value,
                        ),
                        "Recorded observation count": 1,
                        "Expected result/contract": expected_fields(evaluation),
                        "Observed HTTP status(es)": json_value(http.get("status_code")),
                        "Observed response/output": compact_body(http.get("body")),
                        "Browser/secondary observation": browser_summary(browser),
                        "Result": status_text(evaluation.get("status")),
                        "Evaluation reason": str(evaluation.get("reason", "")),
                        "Source evidence": relative(source),
                    }
                )
    return rows


def supplemental_rows(
    supplemental: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[tuple[str, int], dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    candidates: dict[tuple[str, int], dict[str, Any]] = {}

    for cwe in supplemental["cwes"]:
        case_id = str(cwe["cwe_case"])
        for candidate in cwe["candidates"]:
            attempt = int(candidate["attempt"])
            candidates[(case_id, attempt)] = candidate
            source = ROOT / str(candidate["path"])
            document = load_json(source)
            label = candidate_label(case_id, attempt)
            for case in document["cases"]:
                observations = flatten_supplemental_observations(case)
                request_lines: list[str] = []
                status_lines: list[str] = []
                body_lines: list[str] = []
                browser_lines: list[str] = []
                for observation in observations:
                    observation_label = str(observation.get("label", "request"))
                    request_lines.append(
                        f"{observation_label}: GET "
                        f"{normalized_request_target(str(observation.get('url', '')))}"
                    )
                    http = observation.get("http", {})
                    status_lines.append(
                        f"{observation_label}: {json_value(http.get('status_code'))}"
                    )
                    body_lines.append(
                        f"{observation_label}: {compact_body(http.get('body'))}"
                    )
                    browser = browser_summary(observation.get("browser"))
                    if browser:
                        browser_lines.append(f"{observation_label}: {browser}")

                evidence = case.get("evidence", {})
                if not observations and evidence.get("fixture_unavailable"):
                    request_lines.append("Not executed: required fixture unavailable")
                    status_lines.append("No HTTP response")
                    body_lines.append("No output: required fixture unavailable")

                evaluation = case.get("candidate_expectation_evaluation", {})
                rows.append(
                    {
                        "Candidate": label,
                        "CWE": {
                            "xss": "CWE-79",
                            "sqli": "CWE-89",
                            "path-traversal": "CWE-22",
                        }[case_id],
                        "Evidence layer": "supplemental-v1",
                        "Category": str(case["category"]),
                        "Case/Test ID": str(case["test_id"]),
                        "Input/Payload": str(case.get("input", "")),
                        "HTTP method": "GET" if observations else "Not executed",
                        "Effective request(s)": "\n".join(request_lines),
                        "Recorded observation count": len(observations),
                        "Expected result/contract": str(
                            case.get("candidate_expectation", "")
                        ),
                        "Observed HTTP status(es)": "\n".join(status_lines),
                        "Observed response/output": "\n".join(body_lines),
                        "Browser/secondary observation": "\n".join(browser_lines),
                        "Result": status_text(evaluation.get("status")),
                        "Evaluation reason": str(evaluation.get("reason", "")),
                        "Source evidence": relative(source),
                    }
                )
    return rows, candidates


def extension_rows(
    summary: dict[str, Any],
    case_definition: dict[str, Any],
    trial_lookup: dict[str, tuple[str, int]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    case = case_definition["case"]
    oracle = case["candidate_oracle"]
    expected = (
        "HTTP status in "
        f"{json_value(oracle['allowed_status_codes'])}; "
        f"marker_disclosed={json_value(oracle['marker_disclosed'])}"
    )
    for candidate in summary["candidate_results"]:
        source = ROOT / str(candidate["result"])
        result = load_json(source)
        case_id, attempt = trial_lookup[str(candidate["target_id"])]
        response = result["response"]
        evaluation = result["evaluation"]
        request = result["request"]
        rows.append(
            {
                "Candidate": candidate_label(case_id, attempt),
                "CWE": "CWE-22",
                "Evidence layer": "path-s06-extension-v1",
                "Category": "security",
                "Case/Test ID": str(result["case_id"]),
                "Input/Payload": str(request["value"]),
                "HTTP method": str(request["method"]),
                "Effective request(s)": derived_request(
                    str(request["path"]),
                    str(request["parameter"]),
                    str(request["value"]),
                ),
                "Recorded observation count": 1,
                "Expected result/contract": expected,
                "Observed HTTP status(es)": json_value(response.get("status_code")),
                "Observed response/output": compact_body(response.get("body")),
                "Browser/secondary observation": (
                    f"marker_disclosed={json_value(evaluation.get('marker_disclosed'))}; "
                    f"fixture_link={result['fixture']['link']} -> "
                    f"{result['fixture']['target']}"
                ),
                "Result": status_text(evaluation.get("status")),
                "Evaluation reason": str(evaluation.get("reason", "")),
                "Source evidence": relative(source),
            }
        )
    return rows


def human_records(
    primary: dict[str, Any],
    trial_labels: dict[str, str],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    followups: dict[str, dict[str, Any]] = {}
    extension_reviews: dict[str, dict[str, Any]] = {}

    for candidate in primary["experiment_matrix"]:
        adjudication = candidate.get("adjudication") or {}
        if adjudication.get("status") != "completed":
            continue
        source = ROOT / str(adjudication["result"]["path"])
        rows.append(
            {
                "Candidate": trial_labels[str(candidate["trial_id"])],
                "Evidence layer": "primary-v1 original human review",
                "Reviewed on": str(adjudication.get("reviewed_at", ""))[:10],
                "Verdict": str(adjudication.get("verdict", "")),
                "Rationale": str(adjudication.get("rationale", "")),
                "Relationship/notes": "Original review; frozen primary record",
                "Source evidence": relative(source),
            }
        )

    followup_root = ROOT / "data" / "supplemental" / "v1" / "follow-up-reviews"
    for source in sorted(followup_root.glob("*/result.json")):
        result = load_json(source)
        trial_id = str(result["trial_id"])
        followups[trial_id] = result
        rows.append(
            {
                "Candidate": trial_labels[trial_id],
                "Evidence layer": "supplemental-v1 later human review",
                "Reviewed on": str(result.get("reviewed_at", ""))[:10],
                "Verdict": str(result.get("verdict", "")),
                "Rationale": str(result.get("rationale", "")),
                "Relationship/notes": str(
                    result.get(
                        "effect_on_primary_record",
                        "Later qualification; earlier records preserved",
                    )
                ),
                "Source evidence": relative(source),
            }
        )

    extension_root = ROOT / "data" / "extensions" / "path-s06-v1" / "human-reviews"
    for source in sorted(extension_root.glob("*/result.json")):
        result = load_json(source)
        trial_id = str(result["trial_id"])
        extension_reviews[trial_id] = result
        notes = str(result.get("relationship_to_prior_follow_up", ""))
        if result.get("manual_reproduction"):
            notes += "; manual reproduction recorded"
        rows.append(
            {
                "Candidate": trial_labels[trial_id],
                "Evidence layer": "path-s06-extension-v1 later qualification",
                "Reviewed on": str(result.get("reviewed_at", ""))[:10],
                "Verdict": str(result.get("verdict", "")),
                "Rationale": str(result.get("rationale", "")),
                "Relationship/notes": notes,
                "Source evidence": relative(source),
            }
        )

    rows.sort(
        key=lambda row: (
            list(trial_labels.values()).index(row["Candidate"]),
            row["Evidence layer"],
        )
    )
    return rows, followups, extension_reviews


def candidate_summary_rows(
    primary: dict[str, Any],
    supplemental_candidates: dict[tuple[str, int], dict[str, Any]],
    followups: dict[str, dict[str, Any]],
    extension_summary: dict[str, Any],
    extension_reviews: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    extension_results = {
        str(item["target_id"]): item for item in extension_summary["candidate_results"]
    }
    rows: list[dict[str, Any]] = []
    for candidate in sorted(
        primary["experiment_matrix"],
        key=lambda row: (CASE_ORDER[str(row["case_id"])], int(row["attempt"])),
    ):
        case_id = str(candidate["case_id"])
        attempt = int(candidate["attempt"])
        trial_id = str(candidate["trial_id"])
        primary_security = candidate["evidence"]["security"]
        primary_functional = candidate["evidence"]["functional"]
        supplemental = supplemental_candidates[(case_id, attempt)]["summary"]
        by_category = supplemental["by_category"]
        original = candidate.get("adjudication") or {}
        extension = extension_results.get(trial_id)
        rows.append(
            {
                "Candidate": candidate_label(case_id, attempt),
                "Trial ID": trial_id,
                "CWE": str(candidate["cwe"]),
                "Target SAST": str(candidate["evidence"]["target_sast"]).upper(),
                "Primary security": (
                    f"{primary_security['passed']}/{primary_security['total']}"
                ),
                "Primary functional": (
                    f"{primary_functional['passed']}/{primary_functional['total']}"
                ),
                "Automated state": str(candidate["decision"]),
                "Original human": str(
                    original.get("verdict") or "No recorded result"
                ),
                "Supplemental security P/F/I": pfi(by_category.get("security")),
                "Supplemental parity P/F/I": pfi(
                    by_category.get("behavioral_parity")
                ),
                "Supplemental robustness P/F/I": pfi(
                    by_category.get("robustness_contract")
                ),
                "Supplemental later human": str(
                    followups.get(trial_id, {}).get("verdict", "No recorded result")
                ),
                "PATH-S06 extension P/F/I": (
                    "0/1/0" if extension and extension["status"] == "fail" else ""
                ),
                "PATH-S06 later human": str(
                    extension_reviews.get(trial_id, {}).get("verdict", "")
                ),
            }
        )
    return rows


def count_rows(
    primary_details: list[dict[str, Any]],
    supplemental_details: list[dict[str, Any]],
    extension_details: list[dict[str, Any]],
    primary: dict[str, Any],
) -> list[dict[str, Any]]:
    def status_counts(rows: Iterable[dict[str, Any]]) -> Counter[str]:
        return Counter(str(row["Result"]).lower() for row in rows)

    primary_security = [
        row for row in primary_details if row["Category"] == "security"
    ]
    primary_functional = [
        row for row in primary_details if row["Category"] == "functional"
    ]
    supplemental_security = [
        row for row in supplemental_details if row["Category"] == "security"
    ]
    supplemental_parity = [
        row
        for row in supplemental_details
        if row["Category"] == "behavioral_parity"
    ]
    supplemental_robustness = [
        row
        for row in supplemental_details
        if row["Category"] == "robustness_contract"
    ]

    target_resolved = int(primary["metrics"]["sast_remediation_success"]["count"])
    rows = [
        {
            "Evidence layer": "primary-v1",
            "Unit/category": "Target SAST resolution (candidate-level)",
            "Denominator": 15,
            "Pass/resolved": target_resolved,
            "Fail/persistent": 15 - target_resolved,
            "Inconclusive": 0,
            "Meaning": "Five target findings resolved; ten persisted. This is scanner evidence, not an attack result.",
        },
        {
            "Evidence layer": "primary-v1",
            "Unit/category": "Security suite (candidate-level)",
            "Denominator": 15,
            "Pass/resolved": 15,
            "Fail/persistent": 0,
            "Inconclusive": 0,
            "Meaning": "Candidates whose entire registered primary security suite passed.",
        },
        {
            "Evidence layer": "primary-v1",
            "Unit/category": "Functional suite (candidate-level)",
            "Denominator": 15,
            "Pass/resolved": 15,
            "Fail/persistent": 0,
            "Inconclusive": 0,
            "Meaning": "Candidates whose entire registered primary functional suite passed.",
        },
    ]

    for layer, category, values, meaning in (
        (
            "primary-v1",
            "Security test observations",
            primary_security,
            "Individual recorded primary security cases.",
        ),
        (
            "primary-v1",
            "Functional test observations",
            primary_functional,
            "Individual recorded primary functional cases.",
        ),
        (
            "supplemental-v1",
            "Security observations",
            supplemental_security,
            "Frozen supplemental-v1 security cases; five PATH-S06 cases were inconclusive on Windows.",
        ),
        (
            "supplemental-v1",
            "Behavioral parity observations",
            supplemental_parity,
            "Frozen supplemental-v1 comparisons with characterized baseline behavior.",
        ),
        (
            "supplemental-v1",
            "Robustness observations",
            supplemental_robustness,
            "Frozen supplemental-v1 malformed or unusual input contracts.",
        ),
        (
            "path-s06-extension-v1",
            "Security observations",
            extension_details,
            "Separate WSL2 extension; does not replace the five supplemental-v1 inconclusive records.",
        ),
    ):
        counts = status_counts(values)
        rows.append(
            {
                "Evidence layer": layer,
                "Unit/category": category,
                "Denominator": len(values),
                "Pass/resolved": counts["pass"],
                "Fail/persistent": counts["fail"],
                "Inconclusive": counts["inconclusive"],
                "Meaning": meaning,
            }
        )

    supplemental_counts = status_counts(supplemental_details)
    rows.append(
        {
            "Evidence layer": "supplemental-v1",
            "Unit/category": "All supplemental observations",
            "Denominator": len(supplemental_details),
            "Pass/resolved": supplemental_counts["pass"],
            "Fail/persistent": supplemental_counts["fail"],
            "Inconclusive": supplemental_counts["inconclusive"],
            "Meaning": "Mixed categories shown for reconciliation only; not one security success rate.",
        }
    )
    return rows


def rows_for_json(rows: list[dict[str, Any]], headers: list[str]) -> list[dict[str, Any]]:
    return [{header: row.get(header, "") for header in headers} for row in rows]


def write_csv(path: Path, headers: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def excel_column(index: int) -> str:
    value = index
    result = ""
    while value:
        value, remainder = divmod(value - 1, 26)
        result = chr(65 + remainder) + result
    return result


def clean_xml_text(value: Any) -> str:
    text = "" if value is None else str(value)
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", text)
    if len(text) > 32760:
        text = text[:32720] + "\n[Cell text shortened for Excel compatibility]"
    return text


def xml_attribute(value: Any) -> str:
    return escape(clean_xml_text(value), {'"': "&quot;"})


def style_for(header: str, value: Any) -> int:
    text = str(value).strip().lower()
    if header in {"Result", "Target SAST", "Verdict"}:
        if text in {"pass", "resolved"} or "accept_candidate" in text:
            return 2
        if text in {"fail", "persistent"} or "reject_candidate" in text:
            return 3
        if text == "inconclusive" or "request_more_testing" in text:
            return 4
    return 0


def cell_xml(reference: str, value: Any, style: int) -> str:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f'<c r="{reference}" s="{style}"><v>{value}</v></c>'
    text = escape(clean_xml_text(value), {'"': "&quot;"})
    return (
        f'<c r="{reference}" s="{style}" t="inlineStr">'
        f'<is><t xml:space="preserve">{text}</t></is></c>'
    )


def worksheet_xml(
    headers: list[str],
    rows: list[dict[str, Any]],
    widths: list[float],
) -> str:
    last_column = excel_column(len(headers))
    last_row = len(rows) + 1
    columns = "".join(
        f'<col min="{index}" max="{index}" width="{width}" customWidth="1"/>'
        for index, width in enumerate(widths, start=1)
    )
    xml_rows: list[str] = []
    header_cells = "".join(
        cell_xml(f"{excel_column(index)}1", header, 1)
        for index, header in enumerate(headers, start=1)
    )
    xml_rows.append(f'<row r="1" ht="32" customHeight="1">{header_cells}</row>')
    for row_number, row in enumerate(rows, start=2):
        cells = "".join(
            cell_xml(
                f"{excel_column(index)}{row_number}",
                row.get(header, ""),
                style_for(header, row.get(header, "")),
            )
            for index, header in enumerate(headers, start=1)
        )
        xml_rows.append(f'<row r="{row_number}">{cells}</row>')

    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<dimension ref="A1:{last_column}{last_row}"/>'
        '<sheetViews><sheetView workbookViewId="0">'
        '<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'
        '</sheetView></sheetViews>'
        '<sheetFormatPr defaultRowHeight="18"/>'
        f"<cols>{columns}</cols>"
        f"<sheetData>{''.join(xml_rows)}</sheetData>"
        f'<autoFilter ref="A1:{last_column}{last_row}"/>'
        '<pageMargins left="0.25" right="0.25" top="0.5" bottom="0.5" header="0.2" footer="0.2"/>'
        "</worksheet>"
    )


def styles_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="2">
    <font><sz val="11"/><name val="Aptos"/><family val="2"/></font>
    <font><b/><color rgb="FFFFFFFF"/><sz val="11"/><name val="Aptos"/><family val="2"/></font>
  </fonts>
  <fills count="6">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FF173252"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFE8F5F1"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFFBECEA"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFFFF3DE"/><bgColor indexed="64"/></patternFill></fill>
  </fills>
  <borders count="2">
    <border><left/><right/><top/><bottom/><diagonal/></border>
    <border>
      <left style="thin"><color rgb="FFBFD0E5"/></left>
      <right style="thin"><color rgb="FFBFD0E5"/></right>
      <top style="thin"><color rgb="FFBFD0E5"/></top>
      <bottom style="thin"><color rgb="FFBFD0E5"/></bottom>
      <diagonal/>
    </border>
  </borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="5">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="1" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>
    <xf numFmtId="0" fontId="1" fillId="2" borderId="1" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>
    <xf numFmtId="0" fontId="0" fillId="3" borderId="1" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>
    <xf numFmtId="0" fontId="0" fillId="4" borderId="1" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>
    <xf numFmtId="0" fontId="0" fillId="5" borderId="1" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>
  </cellXfs>
  <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
  <dxfs count="0"/>
  <tableStyles count="0" defaultTableStyle="TableStyleMedium2" defaultPivotStyle="PivotStyleLight16"/>
</styleSheet>"""


def build_xlsx(
    path: Path,
    sheets: list[tuple[str, list[str], list[dict[str, Any]], list[float]]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content_types = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>',
    ]
    for index in range(1, len(sheets) + 1):
        content_types.append(
            f'<Override PartName="/xl/worksheets/sheet{index}.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        )
    content_types.append("</Types>")

    workbook_sheets = "".join(
        f'<sheet name="{xml_attribute(name)}" sheetId="{index}" r:id="rId{index}"/>'
        for index, (name, _, _, _) in enumerate(sheets, start=1)
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"<sheets>{workbook_sheets}</sheets>"
        '<calcPr calcId="191029" fullCalcOnLoad="1"/>'
        "</workbook>"
    )
    rels = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
    ]
    for index in range(1, len(sheets) + 1):
        rels.append(
            f'<Relationship Id="rId{index}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            f'Target="worksheets/sheet{index}.xml"/>'
        )
    rels.append(
        f'<Relationship Id="rId{len(sheets) + 1}" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
        'Target="styles.xml"/>'
    )
    rels.append("</Relationships>")

    package_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "".join(content_types))
        archive.writestr("_rels/.rels", package_rels)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", "".join(rels))
        archive.writestr("xl/styles.xml", styles_xml())
        for index, (_, headers, rows, widths) in enumerate(sheets, start=1):
            archive.writestr(
                f"xl/worksheets/sheet{index}.xml",
                worksheet_xml(headers, rows, widths),
            )


def validate_source_counts(
    candidate_rows: list[dict[str, Any]],
    primary_details: list[dict[str, Any]],
    supplemental_details: list[dict[str, Any]],
    extension_details: list[dict[str, Any]],
    human_rows: list[dict[str, Any]],
) -> None:
    assert len(candidate_rows) == 15

    assert len(primary_details) == 100
    assert Counter(row["Category"] for row in primary_details) == {
        "security": 40,
        "functional": 60,
    }
    assert Counter(row["Result"].lower() for row in primary_details) == {"pass": 100}

    assert len(supplemental_details) == 140
    assert Counter(row["Category"] for row in supplemental_details) == {
        "security": 60,
        "behavioral_parity": 45,
        "robustness_contract": 35,
    }
    assert Counter(row["Result"].lower() for row in supplemental_details) == {
        "pass": 120,
        "fail": 15,
        "inconclusive": 5,
    }

    assert len(extension_details) == 5
    assert Counter(row["Result"].lower() for row in extension_details) == {"fail": 5}
    assert all(row["Input/Payload"] == "link/outside-secret.txt" for row in extension_details)
    assert all(row["Observed HTTP status(es)"] == "200" for row in extension_details)
    assert all(
        "FIXPROOF_CONTROLLED_TRAVERSAL_SECRET"
        in row["Observed response/output"]
        for row in extension_details
    )

    assert len(human_rows) == 29
    assert Counter(row["Evidence layer"] for row in human_rows) == {
        "primary-v1 original human review": 10,
        "supplemental-v1 later human review": 14,
        "path-s06-extension-v1 later qualification": 5,
    }


def main() -> None:
    primary = load_json(PRIMARY_REPORT)
    supplemental = load_json(SUPPLEMENTAL_REPORT)
    extension_case = load_json(EXTENSION_CASE)
    extension_summary = load_json(EXTENSION_SUMMARY)

    trial_lookup = {
        str(row["trial_id"]): (str(row["case_id"]), int(row["attempt"]))
        for row in primary["experiment_matrix"]
    }
    trial_labels = {
        trial_id: candidate_label(case_id, attempt)
        for trial_id, (case_id, attempt) in trial_lookup.items()
    }

    primary_details = primary_rows(primary)
    supplemental_details, supplemental_candidates = supplemental_rows(supplemental)
    extension_details = extension_rows(
        extension_summary, extension_case, trial_lookup
    )
    human_rows, followups, extension_reviews = human_records(primary, trial_labels)
    candidate_rows = candidate_summary_rows(
        primary,
        supplemental_candidates,
        followups,
        extension_summary,
        extension_reviews,
    )
    counts = count_rows(
        primary_details,
        supplemental_details,
        extension_details,
        primary,
    )

    validate_source_counts(
        candidate_rows,
        primary_details,
        supplemental_details,
        extension_details,
        human_rows,
    )

    generated_on = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    guide_headers = ["Topic", "Explanation"]
    guide_rows = [
        {
            "Topic": "Purpose",
            "Explanation": "Student-facing trace from candidate-level counts to the recorded payload/request, response/output, and case result.",
        },
        {
            "Topic": "Candidate summary",
            "Explanation": "The primary Security and Functional columns are candidate-level suite results. Supplemental P/F/I columns count individual registered cases.",
        },
        {
            "Topic": "Primary-v1",
            "Explanation": "100 individual runtime observations: 40 security and 60 functional. All passed. Target SAST is a separate candidate-level scanner result.",
        },
        {
            "Topic": "Supplemental-v1",
            "Explanation": "140 frozen observations: 60 security, 45 behavioral parity, and 35 robustness. Outcomes are 120 pass, 15 fail, and 5 inconclusive.",
        },
        {
            "Topic": "PATH-S06 extension",
            "Explanation": "Five separate WSL2 security observations, all failed. These do not replace the five PATH-S06 inconclusive entries in supplemental-v1.",
        },
        {
            "Topic": "Observation count",
            "Explanation": "Each case counts once in the denominator even when its evidence contains two HTTP observations. XSS-S03 references two earlier observations.",
        },
        {
            "Topic": "Request formatting",
            "Explanation": "Primary request targets are deterministically derived from recorded route, query parameter, and payload. Supplemental and extension request targets come from recorded evidence; transient loopback host/ports are omitted.",
        },
        {
            "Topic": "Privacy",
            "Explanation": "Transient local-user paths in generated absolute-path payloads are replaced with descriptive placeholders. This does not change the recorded case outcome.",
        },
        {
            "Topic": "Interpretation",
            "Explanation": "Security, parity, robustness, SAST, and human decisions answer different questions. Do not combine them into one production success rate.",
        },
        {
            "Topic": "Generated on",
            "Explanation": generated_on,
        },
    ]

    sheets = [
        (
            "Guide",
            guide_headers,
            guide_rows,
            [26, 110],
        ),
        (
            "Candidate Summary",
            SUMMARY_HEADERS,
            candidate_rows,
            [16, 39, 11, 15, 16, 17, 28, 24, 22, 22, 24, 27, 24, 28],
        ),
        (
            "Primary Cases",
            DETAIL_HEADERS,
            primary_details,
            [16, 10, 18, 18, 31, 34, 12, 52, 14, 52, 22, 62, 48, 14, 68, 58],
        ),
        (
            "Supplemental Cases",
            DETAIL_HEADERS,
            supplemental_details,
            [16, 10, 20, 21, 16, 40, 13, 65, 14, 55, 26, 70, 55, 14, 68, 65],
        ),
        (
            "PATH-S06 Extension",
            DETAIL_HEADERS,
            extension_details,
            [16, 10, 24, 14, 16, 34, 12, 48, 14, 55, 24, 55, 52, 14, 64, 70],
        ),
        (
            "Count Reconciliation",
            COUNT_HEADERS,
            counts,
            [24, 43, 16, 18, 18, 16, 90],
        ),
        (
            "Human Decisions",
            HUMAN_HEADERS,
            human_rows,
            [16, 39, 16, 34, 110, 58, 72],
        ),
    ]
    build_xlsx(WORKBOOK, sheets)
    PUBLIC_WORKBOOK.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(WORKBOOK, PUBLIC_WORKBOOK)

    CSV_DIR.mkdir(parents=True, exist_ok=True)
    csv_outputs = {
        "candidate-summary.csv": (SUMMARY_HEADERS, candidate_rows),
        "primary-cases.csv": (DETAIL_HEADERS, primary_details),
        "supplemental-cases.csv": (DETAIL_HEADERS, supplemental_details),
        "path-s06-extension.csv": (DETAIL_HEADERS, extension_details),
        "count-reconciliation.csv": (COUNT_HEADERS, counts),
        "human-decisions.csv": (HUMAN_HEADERS, human_rows),
    }
    for filename, (headers, rows) in csv_outputs.items():
        write_csv(CSV_DIR / filename, headers, rows)

    public = {
        "schema_version": "1.0-student-case-evidence",
        "project": "FixProof",
        "generated_on": generated_on,
        "scope_note": (
            "Saved, read-only evidence for the bounded FixProof benchmark. "
            "This export does not execute applications or alter frozen records."
        ),
        "count_note": (
            "Primary candidate-level suite counts and individual observation "
            "counts are distinct. Supplemental categories must remain separate."
        ),
        "candidate_summary": rows_for_json(candidate_rows, SUMMARY_HEADERS),
        "primary_cases": rows_for_json(primary_details, DETAIL_HEADERS),
        "supplemental_cases": rows_for_json(supplemental_details, DETAIL_HEADERS),
        "path_s06_extension": rows_for_json(extension_details, DETAIL_HEADERS),
        "count_reconciliation": rows_for_json(counts, COUNT_HEADERS),
        "human_decisions": rows_for_json(human_rows, HUMAN_HEADERS),
        "downloads": {
            "workbook": WORKBOOK_NAME,
            "appendix": "Video-III-15-candidate-evidence-appendix.pdf",
        },
    }
    PUBLIC_JSON.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(public, ensure_ascii=False, indent=2) + "\n"
    for forbidden in (
        "C:\\Users\\",
        "C:\\\\Users\\\\",
        "/mnt/c/Users/",
        "/home/tony",
        "resp_",
        "OPENAI_API_KEY",
    ):
        assert forbidden not in serialized, f"Public export contains {forbidden!r}"
    PUBLIC_JSON.write_text(serialized, encoding="utf-8")

    with zipfile.ZipFile(WORKBOOK) as archive:
        bad = archive.testzip()
        assert bad is None, f"Invalid XLSX member: {bad}"
        assert len([name for name in archive.namelist() if "/sheet" in name]) == 7

    validation = {
        "schema_version": "1.0",
        "generated_on": generated_on,
        "source_hashes": {
            relative(PRIMARY_REPORT): sha256(PRIMARY_REPORT),
            relative(SUPPLEMENTAL_REPORT): sha256(SUPPLEMENTAL_REPORT),
            relative(EXTENSION_CASE): sha256(EXTENSION_CASE),
            relative(EXTENSION_SUMMARY): sha256(EXTENSION_SUMMARY),
        },
        "counts": {
            "candidates": len(candidate_rows),
            "primary_cases": len(primary_details),
            "primary_security": 40,
            "primary_functional": 60,
            "supplemental_cases": len(supplemental_details),
            "supplemental_pass": 120,
            "supplemental_fail": 15,
            "supplemental_inconclusive": 5,
            "path_s06_extension_cases": len(extension_details),
            "human_decisions": len(human_rows),
        },
        "outputs": {
            relative(WORKBOOK): sha256(WORKBOOK),
            relative(PUBLIC_WORKBOOK): sha256(PUBLIC_WORKBOOK),
            relative(PUBLIC_JSON): sha256(PUBLIC_JSON),
            relative(PUBLIC / "test-evidence.html"): sha256(
                PUBLIC / "test-evidence.html"
            ),
            relative(PUBLIC / "test-evidence.js"): sha256(
                PUBLIC / "test-evidence.js"
            ),
            **{
                relative(CSV_DIR / filename): sha256(CSV_DIR / filename)
                for filename in csv_outputs
            },
        },
        "checks": [
            "15 candidate summary rows",
            "100 primary case rows: 40 security and 60 functional",
            "140 supplemental-v1 rows: 120 pass, 15 fail, 5 inconclusive",
            "5 separate PATH-S06 extension rows: all fail",
            "29 human-decision rows: 10 original, 14 supplemental-v1, 5 extension",
            "public JSON excludes local-user paths, response IDs, and API-key names",
            "XLSX ZIP members passed integrity validation",
            "public HTML and JavaScript hashes recorded; browser validation is separate",
        ],
    }
    VALIDATION.write_text(
        json.dumps(validation, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Created workbook: {WORKBOOK}")
    print(f"Created public data: {PUBLIC_JSON}")
    print(f"Created CSV directory: {CSV_DIR}")
    print(
        "Verified counts: 15 candidates; 100 primary; 140 supplemental-v1; "
        "5 PATH-S06 extension; 29 human decisions"
    )


if __name__ == "__main__":
    main()
