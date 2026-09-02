"use strict";

const REPORT_URL = "/data/evaluation/experiment-report.json";

const byId = (id) => document.getElementById(id);

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = String(text);
  return node;
}

function badge(text, tone) {
  return element("span", `badge ${tone || ""}`.trim(), text);
}

function statusTone(value) {
  const normalized = String(value).toLowerCase();
  if (normalized.includes("pass") || normalized.includes("resolved")) return "pass";
  if (normalized.includes("ready")) return "ready";
  if (normalized.includes("accept")) return "accept";
  if (normalized.includes("complete")) return "completed";
  if (normalized.includes("fail") || normalized.includes("reject")) return "fail";
  if (normalized.includes("inconclusive")) return "inconclusive";
  if (normalized.includes("persistent")) return "persistent";
  if (normalized.includes("adjudication")) return "adjudication";
  return "pending";
}

function titleCase(value) {
  return String(value).replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function decisionLabel(value) {
  const labels = {
    REJECT: "Reject",
    READY_FOR_HUMAN_REVIEW: "Ready for review",
    NEEDS_HUMAN_ADJUDICATION: "Human adjudication",
  };
  return labels[value] || titleCase(value);
}

function rateLabel(metric) {
  if (metric.percentage === null) return `${metric.numerator}/${metric.denominator}`;
  return `${metric.numerator}/${metric.denominator} · ${metric.percentage.toFixed(1)}%`;
}

function renderMetrics(report) {
  const definitions = [
    ["SAST resolved", report.metrics.sast_remediation_success_rate],
    ["Security passed", report.metrics.targeted_security_validation_pass_rate],
    ["Function preserved", report.metrics.functional_preservation_rate],
    ["Adjudications complete", report.metrics.human_adjudication_completion_rate],
  ];
  const grid = byId("metric-grid");
  grid.replaceChildren();

  definitions.forEach(([label, metric]) => {
    const card = element("article", "metric-card");
    card.append(element("p", "metric-label", label));
    card.append(element("p", "metric-value", rateLabel(metric)));
    const meter = element("progress", "meter");
    meter.setAttribute("role", "meter");
    meter.setAttribute("aria-label", label);
    meter.setAttribute("aria-valuemin", "0");
    meter.setAttribute("aria-valuemax", "100");
    meter.setAttribute("aria-valuenow", String(metric.percentage || 0));
    meter.max = 100;
    meter.value = Math.max(0, Math.min(100, metric.percentage || 0));
    card.append(meter);
    grid.append(card);
  });
}

function renderCoverage(report) {
  const list = byId("coverage-list");
  list.replaceChildren();
  Object.entries(report.outcome_coverage.required_outcomes).forEach(([name, outcome]) => {
    const item = element("div", "coverage-item");
    const copy = element("div");
    copy.append(element("strong", "", titleCase(name)));
    let source = "Not covered";
    if (outcome.observed_in_primary_ai_attempts) source = "Primary AI attempt";
    else if (outcome.demonstrated_by_non_ai_control) source = "Separated non-AI control";
    copy.append(element("div", "coverage-source", source));
    item.append(copy, badge(outcome.covered ? "Covered" : "Missing", outcome.covered ? "pass" : "fail"));
    list.append(item);
  });
}

function renderAdjudication(report) {
  const summary = report.adjudication_summary;
  const container = byId("adjudication-summary");
  container.replaceChildren();
  [
    ["Required", summary.required],
    ["Completed", summary.completed],
    ["Pending", summary.pending + summary.missing_packet],
  ].forEach(([label, value]) => {
    const item = element("div", "review-stat");
    item.append(element("span", "", label), element("strong", "", value));
    container.append(item);
  });
}

function evidenceLabel(status, counts) {
  const base = titleCase(status);
  if (!counts) return base;
  return `${base} (${counts.passed}/${counts.total})`;
}

function renderMatrix(report, onSelect) {
  const body = byId("matrix-body");
  body.replaceChildren();
  report.experiment_matrix.forEach((row, index) => {
    const tr = element("tr");
    tr.tabIndex = 0;
    tr.dataset.index = String(index);
    const values = [row.case, row.cwe, row.attempt];
    values.forEach((value) => tr.append(element("td", "", value)));

    const sastCell = element("td");
    sastCell.append(badge(titleCase(row.evidence.target_sast), statusTone(row.evidence.target_sast)));
    tr.append(sastCell);
    const securityCell = element("td");
    securityCell.append(badge(evidenceLabel(row.evidence.security.status, row.evidence.security), statusTone(row.evidence.security.status)));
    tr.append(securityCell);
    const functionalCell = element("td");
    functionalCell.append(badge(evidenceLabel(row.evidence.functional.status, row.evidence.functional), statusTone(row.evidence.functional.status)));
    tr.append(functionalCell);
    tr.append(element("td", "", row.evidence.new_sast_findings));
    const decisionCell = element("td");
    decisionCell.append(badge(decisionLabel(row.decision), statusTone(row.decision)));
    tr.append(decisionCell);

    const select = () => onSelect(index);
    tr.addEventListener("click", select);
    tr.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        select();
      }
    });
    body.append(tr);
  });
}

function evidenceCard(label, value, tone) {
  const card = element("div", "evidence-card");
  card.append(element("span", "", label), badge(value, tone));
  return card;
}

function artifactList(artifacts) {
  const list = element("dl", "artifact-list");
  Object.entries(artifacts).forEach(([name, record]) => {
    const item = element("div", "artifact-item");
    item.append(element("dt", "", titleCase(name)));
    const description = element("dd");
    description.textContent = record.path;
    description.title = `${record.path}\nSHA-256: ${record.sha256}`;
    item.append(description);
    list.append(item);
  });
  return list;
}

function renderAttemptDetail(row) {
  const container = byId("attempt-detail");
  container.replaceChildren();

  const heading = element("div", "detail-title");
  const copy = element("div");
  copy.append(element("h3", "", `${row.case} · ${row.cwe} · Attempt ${row.attempt}`));
  copy.append(element("p", "", `${row.canonical_id} · ${row.model}`));
  heading.append(copy, badge(decisionLabel(row.decision), statusTone(row.decision)));
  container.append(heading);

  const evidence = element("div", "evidence-grid");
  evidence.append(
    evidenceCard("Syntax", titleCase(row.evidence.syntax), statusTone(row.evidence.syntax)),
    evidenceCard("Target SAST", titleCase(row.evidence.target_sast), statusTone(row.evidence.target_sast)),
    evidenceCard("Security", evidenceLabel(row.evidence.security.status, row.evidence.security), statusTone(row.evidence.security.status)),
    evidenceCard("Functional", evidenceLabel(row.evidence.functional.status, row.evidence.functional), statusTone(row.evidence.functional.status)),
  );
  container.append(evidence);

  const columns = element("div", "detail-columns");
  const interpretation = element("section", "detail-section");
  interpretation.append(element("h3", "", "Interpretation"));
  const facts = element("ul");
  [
    `Classification: ${row.classification}`,
    `New SAST findings: ${row.evidence.new_sast_findings}`,
    `Rule origin: ${row.scanner_evidence.rule_origins.join(", ")}`,
    `Candidate origin: ${row.candidate_origin}`,
    `Human review: ${row.adjudication.status}`,
  ].forEach((fact) => facts.append(element("li", "", fact)));
  if (row.adjudication.verdict) facts.append(element("li", "", `Human verdict: ${row.adjudication.verdict}`));
  if (row.evidence_revision) {
    facts.append(element("li", "", `Evidence revision: ${row.evidence_revision.revision}`));
    const historical = row.evidence_revision.historical_adjudication;
    if (historical) {
      facts.append(element("li", "", `Historical review: ${historical.verdict} by ${historical.reviewer}`));
    }
  }
  interpretation.append(facts);

  const artifacts = element("section", "detail-section");
  artifacts.append(element("h3", "", "Bound artifacts"), artifactList(row.artifacts));
  columns.append(interpretation, artifacts);
  container.append(columns);
}

function renderControls(report) {
  const container = byId("control-list");
  container.replaceChildren();
  report.outcome_coverage_controls.forEach((row) => {
    const card = element("article", "control-card");
    const copy = element("div", "control-copy");
    copy.append(element("h3", "", row.case));
    copy.append(element("p", "", `${row.candidate_origin} · ${row.metric_scope}`));
    card.append(copy);
    [
      ["SAST", titleCase(row.evidence.target_sast), statusTone(row.evidence.target_sast)],
      ["Security", titleCase(row.evidence.security.status), statusTone(row.evidence.security.status)],
      ["Functional", titleCase(row.evidence.functional.status), statusTone(row.evidence.functional.status)],
      ["Classification", row.classification, row.evidence.false_success ? "fail" : "pass"],
    ].forEach(([label, value, tone]) => {
      const stat = element("div", "control-stat");
      stat.append(element("span", "", label), badge(value, tone));
      card.append(stat);
    });
    container.append(card);
  });
}

function initializePicker(report, selectAttempt) {
  const picker = byId("attempt-picker");
  picker.replaceChildren();
  report.experiment_matrix.forEach((row, index) => {
    const option = element("option", "", `${row.case} · Attempt ${row.attempt}`);
    option.value = String(index);
    picker.append(option);
  });
  picker.addEventListener("change", () => selectAttempt(Number(picker.value)));
}

function renderReport(report) {
  byId("study-summary").textContent = `${report.case_count} cases · ${report.attempt_count} AI attempts · ${report.control_count} separated control`;
  byId("report-state").textContent = "Report loaded · integrity-selected artifacts";
  byId("manifest-digest").textContent = `Manifest ${report.manifest.sha256.slice(0, 12)}…`;
  renderMetrics(report);
  renderCoverage(report);
  renderAdjudication(report);
  renderControls(report);

  const picker = byId("attempt-picker");
  const selectAttempt = (index) => {
    picker.value = String(index);
    document.querySelectorAll("#matrix-body tr").forEach((row, rowIndex) => {
      row.classList.toggle("is-selected", rowIndex === index);
      row.setAttribute("aria-selected", String(rowIndex === index));
    });
    renderAttemptDetail(report.experiment_matrix[index]);
  };
  initializePicker(report, selectAttempt);
  renderMatrix(report, selectAttempt);
  selectAttempt(0);
}

async function loadReport() {
  try {
    const response = await fetch(REPORT_URL, { cache: "no-store" });
    if (!response.ok) throw new Error(`Report request failed with HTTP ${response.status}.`);
    const report = await response.json();
    if (!Array.isArray(report.experiment_matrix) || !report.metrics) {
      throw new Error("The report JSON does not contain the expected FixProof schema.");
    }
    renderReport(report);
    byId("dashboard").setAttribute("aria-busy", "false");
  } catch (error) {
    byId("dashboard").hidden = true;
    byId("error-message").textContent = error instanceof Error ? error.message : String(error);
    byId("error-panel").hidden = false;
    byId("report-state").textContent = "Report unavailable";
  }
}

loadReport();
