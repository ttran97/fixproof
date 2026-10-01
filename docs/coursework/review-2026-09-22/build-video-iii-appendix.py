"""Build a source-bound, printable Video III evidence appendix.

This reads only saved primary/supplemental evidence and writes derived HTML/PDF
beside the script. It does not change the frozen study or human review records.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
from collections import Counter
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PRIMARY_REPORT = ROOT / "data/evaluation/primary-report.json"
SUPPLEMENTAL_REPORT = ROOT / "data/supplemental/v1/supplemental-report.json"
FOLLOW_UP_DIR = ROOT / "data/supplemental/v1/follow-up-reviews"
EXTENSION_RUN_ID = "20260930T180925912688Z-path-s06-v1"
EXTENSION_SUMMARY = (
    ROOT
    / "data/extensions/path-s06-v1/runs"
    / EXTENSION_RUN_ID
    / "summary.json"
)
EXTENSION_FOLLOW_UP_DIR = ROOT / "data/extensions/path-s06-v1/human-reviews"
OUTPUT_HTML = HERE / "Video-III-15-candidate-evidence-appendix.html"
OUTPUT_PDF = HERE / "Video-III-15-candidate-evidence-appendix.pdf"
CASE_ORDER = {"xss": 0, "sqli": 1, "path-traversal": 2}
CASE_LABEL = {"xss": "XSS", "sqli": "SQLi", "path-traversal": "Traversal"}
CATEGORIES = ("security", "behavioral_parity", "robustness_contract")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def checked_binding(binding: dict) -> tuple[dict, str]:
    relative = binding["path"]
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT.resolve()) or not path.is_file():
        raise ValueError(f"Bound source is outside the repository or missing: {relative}")
    data = path.read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    if actual != binding["sha256"]:
        raise ValueError(f"Saved evidence hash mismatch: {relative}")
    return json.loads(data.decode("utf-8-sig")), relative


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def key_for(row: dict) -> tuple[str, int]:
    return row["case_id"], int(row["attempt"])


def trial_name(case: str, attempt: int) -> str:
    return f"{CASE_LABEL[case]} {attempt:02d}"


def original_label(record: dict | None) -> str:
    if record is None:
        return "No human result"
    return {
        "ACCEPT_CANDIDATE": "Accept candidate",
        "REQUEST_ADDITIONAL_TESTING": "Request more testing",
    }.get(record["verdict"], record["verdict"])


def policy_label(value: str) -> str:
    return {
        "READY_FOR_HUMAN_REVIEW": "Ready for review",
        "NEEDS_HUMAN_ADJUDICATION": "Needs adjudication",
        "REJECT": "Reject",
    }.get(value, value)


def category_counts(summary: dict, category: str) -> str:
    block = summary["by_category"][category]
    return f"{block['pass']}/{block['fail']}/{block['inconclusive']}"


def follow_up_label(record: dict | None) -> str:
    if record is None:
        return "No supplemental result"
    return {
        "FOLLOW_UP_ACCEPT_CANDIDATE": "Bounded accept",
        "FOLLOW_UP_REJECT_CANDIDATE": "Reject candidate",
        "FOLLOW_UP_REQUEST_MORE_TESTING": "Request more testing",
    }.get(record["verdict"], record["verdict"])


def html_source_path(path: str) -> str:
    return f'<span class="source-path">{esc(path)}</span>'


def rationale_block(kind: str, result: dict, source: str) -> str:
    payload = result
    rationale = payload.get("rationale", "")
    if not rationale.strip():
        raise ValueError(f"Empty human rationale in {source}")
    return (
        f'<div class="rationale-group"><h4>{esc(kind)} — '
        f'{esc(payload["verdict"])}</h4>'
        f'<p class="metadata">Reviewer: {esc(payload["reviewer"])} · '
        f'Recorded: {esc(payload["reviewed_at"])}<br>'
        f'Source: {html_source_path(source)}</p>'
        f'<div class="rationale">{esc(rationale)}</div></div>'
    )


def build_html(rows: list[dict], category_totals: dict) -> str:
    primary_rows = []
    supplemental_rows = []
    details = []

    for item in rows:
        primary = item["primary"]
        supplemental = item["supplemental"]
        original = item["original"]
        later = item["later"]
        extension = item["extension"]
        extension_review = item["extension_review"]
        case, attempt = key_for(primary)
        name = trial_name(case, attempt)
        anchor = primary["trial_id"]
        evidence = primary["evidence"]
        summary = supplemental["summary"]
        nonpassing = item["nonpassing_tests"]
        nonpassing_text = ", ".join(
            f'{entry["test_id"]} ({entry["status"]})' for entry in nonpassing
        ) or "None in registered supplement"
        follow_label = follow_up_label(later)
        extension_label = (
            f'{extension["evaluation"]["status"].title()} · '
            f'{follow_up_label(extension_review)}'
            if extension is not None
            else "Not applicable"
        )

        primary_rows.append(
            f'<tr class="case-{esc(case)}">'
            f'<td><a href="#{esc(anchor)}">{esc(name)}</a></td>'
            f'<td>{esc(evidence["target_sast"])}</td>'
            f'<td>{evidence["security"]["passed"]}/{evidence["security"]["total"]}</td>'
            f'<td>{evidence["functional"]["passed"]}/{evidence["functional"]["total"]}</td>'
            f'<td>{esc(policy_label(primary["decision"]))}</td>'
            f'<td>{esc(original_label(original))}</td>'
            f'<td>{esc(follow_label)}</td></tr>'
        )
        supplemental_rows.append(
            f'<tr class="case-{esc(case)}">'
            f'<td><a href="#{esc(anchor)}">{esc(name)}</a></td>'
            f'<td>{category_counts(summary, "security")}</td>'
            f'<td>{category_counts(summary, "behavioral_parity")}</td>'
            f'<td>{category_counts(summary, "robustness_contract")}</td>'
            f'<td>{esc(nonpassing_text)}</td>'
            f'<td>{esc(follow_label)}</td>'
            f'<td>{esc(extension_label)}</td></tr>'
        )

        original_html = (
            rationale_block("Original primary human review", original, item["original_path"])
            if original
            else '<p class="no-record">No original human verdict or rationale is recorded. '
            'The automated state was readiness for human review, not approval.</p>'
        )
        later_html = (
            rationale_block("Supplemental human review", later, item["later_path"])
            if later
            else '<p class="no-record">No separate supplemental human verdict or rationale is recorded.</p>'
        )
        extension_html = (
            rationale_block(
                "PATH-S06 extension human qualification",
                extension_review,
                item["extension_review_path"],
            )
            if extension_review
            else ""
        )
        extension_summary = (
            f' PATH-S06 extension: {esc(extension["evaluation"]["status"])}; '
            f'HTTP {extension["response"]["status_code"]}; outside marker '
            f'disclosed: {esc(extension["evaluation"]["marker_disclosed"])}.'
            if extension is not None
            else ""
        )
        details.append(
            f'<section class="candidate-detail" id="{esc(anchor)}">'
            f'<h3>{esc(name)} <span class="muted">· {esc(primary["cwe"])} · '
            f'{esc(anchor)}</span></h3>'
            f'<p class="detail-summary">Primary target SAST: {esc(evidence["target_sast"])}; '
            f'automated state: {esc(primary["decision"])}. Supplemental cases: '
            f'{summary["pass"]} pass, {summary["fail"]} fail, '
            f'{summary["inconclusive"]} inconclusive. Nonpassing: '
            f'{esc(nonpassing_text)}.{extension_summary}</p>'
            f'<p class="metadata">Primary decision: '
            f'{html_source_path(primary["artifacts"]["decision"]["path"])}<br>'
            f'Supplemental candidate result: {html_source_path(item["supplemental_path"])}</p>'
            f'{original_html}{later_html}{extension_html}</section>'
        )

    totals = category_totals
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>FixProof — 15-candidate evidence appendix</title>
  <style>
    @page {{ size: 16in 9in; margin: 0.55in 0.65in; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; color: #17253b; background: white; font: 16px/1.35 Arial, Helvetica, sans-serif; }}
    h1 {{ font-size: 34px; margin: 0 0 12px; color: #17345a; }}
    h2 {{ font-size: 25px; margin: 20px 0 9px; color: #17345a; }}
    h3 {{ font-size: 20px; margin: 0 0 8px; color: #17345a; }}
    h4 {{ font-size: 17px; margin: 13px 0 5px; color: #4b3572; }}
    p {{ margin: 8px 0; }}
    .muted, .metadata {{ color: #52657d; }}
    .metadata {{ font-size: 12px; overflow-wrap: anywhere; }}
    .intro {{ max-width: 1240px; }}
    .callout {{ border-left: 5px solid #d5a357; background: #fff7e8; padding: 10px 15px; margin: 15px 0; }}
    .metric-strip {{ display: flex; gap: 10px; margin: 16px 0 20px; }}
    .metric {{ flex: 1; padding: 11px 13px; background: #eef5fd; border: 1px solid #c5d8ec; border-radius: 10px; }}
    .metric strong {{ display: block; font-size: 20px; color: #17345a; }}
    .metric span {{ font-size: 13px; color: #52657d; }}
    .page-break {{ break-before: page; }}
    table {{ width: 100%; border-collapse: collapse; table-layout: fixed; font-size: 13px; }}
    th, td {{ border-bottom: 1px solid #d9e3ef; padding: 7px 8px; text-align: left; vertical-align: top; overflow-wrap: anywhere; }}
    th {{ background: #183959; color: white; font-size: 12px; }}
    tbody tr:nth-child(even) {{ background: #f6f9fc; }}
    tbody tr.case-sqli td:first-child {{ border-left: 4px solid #d4ab67; }}
    tbody tr.case-xss td:first-child {{ border-left: 4px solid #8fb1d7; }}
    tbody tr.case-path-traversal td:first-child {{ border-left: 4px solid #a6d0bd; }}
    a {{ color: #174f8d; text-decoration: none; }}
    .note {{ font-size: 14px; color: #455a73; margin-top: 15px; }}
    .candidate-detail {{ border-top: 2px solid #c5d8ec; padding: 15px 0 17px; break-inside: avoid; }}
    .candidate-detail:first-of-type {{ border-top: 0; }}
    .detail-summary {{ font-size: 14px; }}
    .rationale-group {{ margin: 9px 0 14px; }}
    .rationale {{ white-space: pre-wrap; overflow-wrap: anywhere; padding: 10px 13px; border-left: 4px solid #ad9bcb; background: #f8f6fc; font-size: 13px; line-height: 1.32; }}
    .no-record {{ color: #626e7d; font-style: italic; font-size: 14px; }}
    .source-path {{ font-family: Consolas, 'Courier New', monospace; }}
    @media screen {{ body {{ max-width: 1500px; margin: 30px auto; padding: 0 25px; }} .page-break {{ border-top: 3px dashed #d9e3ef; margin-top: 45px; padding-top: 20px; }} }}
  </style>
</head>
<body>
  <section>
    <h1>FixProof · 15-candidate evidence appendix</h1>
    <p class="intro">Updated September 30, 2026 from verified saved evidence. This is a reference handout, not a replacement for the frozen primary or supplemental-v1 reports. It includes all 15 candidate-level outcomes and the <em>complete recorded text</em> of original, supplemental-v1, and PATH-S06 extension human rationales.</p>
    <div class="metric-strip">
      <div class="metric"><strong>15 primary attempts</strong><span>Five initial calls per controlled CWE fixture</span></div>
      <div class="metric"><strong>10 original reviews</strong><span>Seven acceptances; three additional-testing requests</span></div>
      <div class="metric"><strong>14 supplemental human records</strong><span>5 reject · 5 bounded accept · 4 request more testing</span></div>
      <div class="metric"><strong>5 PATH-S06 qualifications</strong><span>5 later reject · 1 manually reproduced</span></div>
    </div>
    <div class="callout"><strong>How to read this:</strong> “Ready for review” is an automated state, not a human approval. Supplemental-v1 retains 140 observations and 14 human records. The five PATH-S06 failures and human qualifications are a separate later extension; they do not overwrite primary-v1 or supplemental-v1.</div>
    <h2>1. Frozen primary-v1 matrix</h2>
    <table aria-label="Primary results for all fifteen candidates">
      <colgroup><col style="width:10%"><col style="width:11%"><col style="width:11%"><col style="width:11%"><col style="width:20%"><col style="width:20%"><col style="width:17%"></colgroup>
      <thead><tr><th>Candidate</th><th>Target SAST</th><th>Security pass</th><th>Functional pass</th><th>Automated state</th><th>Original human</th><th>Supplemental human</th></tr></thead>
      <tbody>{''.join(primary_rows)}</tbody>
    </table>
    <p class="note">Primary security and functional columns are passed/registered checks from the original suite. Every one of the 15 candidates passed those fixed suites. Five target SAST findings resolved; ten persisted while runtime checks passed. The five SQLi candidates had no original primary human verdict; their bounded acceptances are separate September 22 supplemental human records.</p>
  </section>

  <section class="page-break">
    <h2>2. Supplemental-v1 matrix — same 15 saved candidates</h2>
    <p class="intro">The supplemental protocol first characterized three baselines, then ran registered cases against the saved candidates in disposable copies. It made no new model calls and did not rerun primary SAST.</p>
    <div class="metric-strip">
      <div class="metric"><strong>Security</strong><span>{totals['security']['pass']} pass · {totals['security']['fail']} fail · {totals['security']['inconclusive']} inconclusive</span></div>
      <div class="metric"><strong>Behavioral parity</strong><span>{totals['behavioral_parity']['pass']} pass · {totals['behavioral_parity']['fail']} fail · {totals['behavioral_parity']['inconclusive']} inconclusive</span></div>
      <div class="metric"><strong>Robustness</strong><span>{totals['robustness_contract']['pass']} pass · {totals['robustness_contract']['fail']} fail · {totals['robustness_contract']['inconclusive']} inconclusive</span></div>
    </div>
    <p class="note"><strong>P/F/I</strong> means pass/fail/inconclusive. Nonpassing case IDs identify failures or unexecuted cases; they are not interchangeable. `PATH-S06` remains inconclusive in supplemental-v1 because the Windows symlink fixture could not be created. Its later WSL2 extension result is shown in the final column.</p>
    <table aria-label="Supplemental results for all fifteen saved candidates">
      <colgroup><col style="width:9%"><col style="width:11%"><col style="width:11%"><col style="width:11%"><col style="width:29%"><col style="width:14%"><col style="width:15%"></colgroup>
      <thead><tr><th>Candidate</th><th>Security P/F/I</th><th>Parity P/F/I</th><th>Robustness P/F/I</th><th>Nonpassing registered cases</th><th>Supplemental-v1 human</th><th>PATH-S06 extension</th></tr></thead>
      <tbody>{''.join(supplemental_rows)}</tbody>
    </table>
    <p class="note">XSS 01, 02, 04, and 05 each failed the frozen missing-name parity case `XSS-P01`; XSS 03 passed all nine registered XSS supplemental cases. SQLi `SQL-R01` remains failed even though the bounded repair was accepted. Within supplemental-v1, Traversal 02–05 retain request-more-testing records and PATH-S06 remains inconclusive. The separate extension later recorded HTTP 200 marker disclosure and a rejection qualification for all five traversal candidates.</p>
  </section>

  <section class="page-break">
    <h2>3. Complete human rationale records</h2>
    <p class="intro">Text below is copied verbatim from bound `result.json` rationale fields, including original primary review wording, supplemental-v1 decisions, and PATH-S06 extension qualifications. The source path and recorded timestamp accompany each statement. The five SQLi entries have no original primary human result; their September 22 bounded acceptances are shown separately and were not inferred automatically from `READY_FOR_HUMAN_REVIEW`.</p>
    {''.join(details)}
  </section>

  <section class="page-break">
    <h2>Evidence and interpretation boundary</h2>
    <p>This appendix was assembled from <span class="source-path">data/evaluation/primary-report.json</span>, <span class="source-path">data/supplemental/v1/supplemental-report.json</span>, ten bound primary review results, fourteen bound supplemental human results, fifteen hash-checked supplemental candidate results, five PATH-S06 extension results, and five extension human qualifications. The generated appendix does not alter those files.</p>
    <p>The main study concerns three deliberately vulnerable Express fixtures and repeated AI repair proposals, not fifteen independent applications or a representative web-app corpus. Passing registered tests does not establish production safety. A copied workspace preserves experiment inputs but is not a security sandbox.</p>
    <p>The primary reviewer decisions were recorded at their original times. Supplemental-v1 and PATH-S06 extension records apply later evidence without changing earlier states, reviews, or metrics. A bounded acceptance does not turn a robustness failure into a pass, and the supplemental-v1 inconclusive outcomes remain inconclusive even though the separate extension later executed the case. For raw observations, patches, or packet bindings, use the source paths in each candidate entry.</p>
  </section>
</body>
</html>
"""


def main() -> None:
    primary_report = load_json(PRIMARY_REPORT)
    supplemental_report = load_json(SUPPLEMENTAL_REPORT)
    if primary_report.get("evidence_verified") is not True:
        raise ValueError("Primary report is not marked verified.")
    if supplemental_report.get("evidence_verified") is not True:
        raise ValueError("Supplemental report is not marked verified.")

    primary_rows = primary_report["experiment_matrix"]
    if len(primary_rows) != 15:
        raise ValueError("Expected the frozen 15-attempt primary matrix.")
    primary_by_key = {key_for(row): row for row in primary_rows}
    if len(primary_by_key) != 15 or Counter(row["case_id"] for row in primary_rows) != {
        "xss": 5, "sqli": 5, "path-traversal": 5
    }:
        raise ValueError("Primary case/attempt schedule is not 5 per CWE.")

    supplemental_by_key = {}
    for case in supplemental_report["cwes"]:
        for binding in case["candidates"]:
            key = case["cwe_case"], int(binding["attempt"])
            result, path = checked_binding(binding)
            if result["summary"] != binding["summary"]:
                raise ValueError(f"Supplemental summary mismatch: {key}")
            actual_nonpassing = [
                {
                    "test_id": case_result["test_id"],
                    "category": case_result["category"],
                    "status": case_result["candidate_expectation_evaluation"]["status"],
                }
                for case_result in result["cases"]
                if case_result["candidate_expectation_evaluation"]["status"] != "pass"
            ]
            if actual_nonpassing != binding["nonpassing_tests"]:
                raise ValueError(f"Supplemental nonpassing cases mismatch: {key}")
            if key in supplemental_by_key:
                raise ValueError(f"Duplicate supplemental candidate: {key}")
            supplemental_by_key[key] = result, path, actual_nonpassing
    if set(supplemental_by_key) != set(primary_by_key):
        raise ValueError("Supplemental and primary candidate schedules differ.")

    followups = {}
    for path in sorted(FOLLOW_UP_DIR.glob("*/result.json")):
        result = load_json(path)
        trial_id = result["trial_id"]
        if trial_id in followups or result["status"] != "completed":
            raise ValueError(f"Duplicate or incomplete follow-up: {trial_id}")
        checked_binding(result["packet"])
        checked_binding(result["supplemental_candidate_result"])
        if result["effect_on_primary_record"] != "none_original_record_is_preserved":
            raise ValueError(f"Follow-up may overwrite primary evidence: {trial_id}")
        followups[trial_id] = result, path.relative_to(ROOT).as_posix()

    extension_summary = load_json(EXTENSION_SUMMARY)
    if (
        extension_summary.get("status") != "complete"
        or extension_summary.get("candidate_counts")
        != {"pass": 0, "fail": 5, "inconclusive": 0}
        or extension_summary.get("protected_data_unchanged") is not True
    ):
        raise ValueError("PATH-S06 extension summary is incomplete or unexpected.")
    extension_results = {}
    for binding in extension_summary["candidate_results"]:
        result, path = checked_binding(
            {"path": binding["result"], "sha256": binding["sha256"]}
        )
        trial_id = binding["target_id"]
        if (
            result["evaluation"]["status"] != "fail"
            or result["evaluation"]["marker_disclosed"] is not True
            or result["response"]["status_code"] != 200
        ):
            raise ValueError(f"Unexpected PATH-S06 outcome: {trial_id}")
        extension_results[trial_id] = result, path

    extension_followups = {}
    for path in sorted(EXTENSION_FOLLOW_UP_DIR.glob("*/result.json")):
        result = load_json(path)
        trial_id = result["trial_id"]
        if trial_id in extension_followups or result["status"] != "completed":
            raise ValueError(f"Duplicate or incomplete extension review: {trial_id}")
        checked_binding(result["approval"])
        packet, _ = checked_binding(result["packet"])
        checked_binding(result["extension_candidate_result"])
        if result["extension_candidate_result"] != packet["extension_candidate_result"]:
            raise ValueError(f"Extension review links another result: {trial_id}")
        if result["effect_on_frozen_records"] != "none_earlier_records_are_preserved":
            raise ValueError(f"Extension review may overwrite prior evidence: {trial_id}")
        extension_followups[trial_id] = result, path.relative_to(ROOT).as_posix()
    if len(extension_results) != 5 or len(extension_followups) != 5:
        raise ValueError("Expected five PATH-S06 results and five qualifications.")

    rows = []
    original_count = 0
    for key in sorted(primary_by_key, key=lambda value: (CASE_ORDER[value[0]], value[1])):
        primary = primary_by_key[key]
        supplemental, supplemental_path, nonpassing_tests = supplemental_by_key[key]
        review_binding = primary["artifacts"].get("adjudication_result")
        if review_binding:
            review_file, review_path = checked_binding(review_binding)
            original = review_file["adjudication_result"]
            if original["verdict"] != primary["adjudication"]["verdict"]:
                raise ValueError(f"Primary review verdict mismatch: {key}")
            original_count += 1
        else:
            original = None
            review_path = ""
            if primary["decision"] != "READY_FOR_HUMAN_REVIEW":
                raise ValueError(f"Missing required original review: {key}")
        later, later_path = followups.get(primary["trial_id"], (None, ""))
        if later and later["supplemental_candidate_result"]["path"] != supplemental_path:
            raise ValueError(f"Follow-up links another candidate result: {key}")
        extension, extension_path = extension_results.get(
            primary["trial_id"], (None, "")
        )
        extension_review, extension_review_path = extension_followups.get(
            primary["trial_id"], (None, "")
        )
        if (extension is None) != (extension_review is None):
            raise ValueError(f"Incomplete extension evidence pair: {key}")
        rows.append({
            "primary": primary,
            "supplemental": supplemental,
            "supplemental_path": supplemental_path,
            "nonpassing_tests": nonpassing_tests,
            "original": original,
            "original_path": review_path,
            "later": later,
            "later_path": later_path,
            "extension": extension,
            "extension_path": extension_path,
            "extension_review": extension_review,
            "extension_review_path": extension_review_path,
        })

    follow_up_counts = Counter(
        result["verdict"] for result, _ in followups.values()
    )
    expected_follow_up_counts = Counter({
        "FOLLOW_UP_REJECT_CANDIDATE": 5,
        "FOLLOW_UP_ACCEPT_CANDIDATE": 5,
        "FOLLOW_UP_REQUEST_MORE_TESTING": 4,
    })
    if original_count != 10 or follow_up_counts != expected_follow_up_counts:
        raise ValueError(
            "Expected ten original reviews and 14 supplemental human records "
            "split 5 reject, 5 accept, and 4 request-more-testing."
        )
    if sum(row["supplemental"]["summary"]["registered"] for row in rows) != 140:
        raise ValueError("Supplemental observation total is not 140.")
    for category in CATEGORIES:
        actual = {
            field: sum(
                row["supplemental"]["summary"]["by_category"][category][field]
                for row in rows
            )
            for field in ("total", "pass", "fail", "inconclusive")
        }
        if actual != supplemental_report["candidate_observations_by_category"][category]:
            raise ValueError(f"Supplemental category totals differ: {category}")

    document = build_html(rows, supplemental_report["candidate_observations_by_category"])
    rationales = [
        review["rationale"]
        for row in rows
        for review in (row["original"], row["later"], row["extension_review"])
        if review is not None
    ]
    if (
        len(rationales) != 29
        or any(esc(rationale) not in document for rationale in rationales)
        or document.count('<tr class="case-') != 30
        or document.count('class="candidate-detail"') != 15
        or document.count('<div class="rationale">') != 29
    ):
        raise ValueError("Generated appendix is missing a matrix row, detail, or rationale.")
    OUTPUT_HTML.write_text(document, encoding="utf-8")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1600, "height": 900})
            page.goto(OUTPUT_HTML.as_uri(), wait_until="load")
            page.pdf(
                path=str(OUTPUT_PDF),
                print_background=True,
                prefer_css_page_size=True,
                display_header_footer=False,
            )
        finally:
            browser.close()
    pdf_bytes = OUTPUT_PDF.read_bytes()
    page_count = len(re.findall(rb"/Type\s*/Page\b", pdf_bytes))
    if not pdf_bytes.startswith(b"%PDF-") or page_count < 3:
        raise ValueError("PDF generation did not produce the complete appendix.")
    print(
        f"Wrote {OUTPUT_HTML.name} and {OUTPUT_PDF.name}: "
        f"15 candidates, 10 original rationales, 14 supplemental rationales, "
        f"5 PATH-S06 rationales, {page_count} PDF pages."
    )


if __name__ == "__main__":
    main()
