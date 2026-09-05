"use strict";

function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (className) element.className = className;
  return element;
}

function showTrial(row) {
  document.getElementById("primary-detail").hidden = false;
  document.getElementById("detail-heading").textContent = row.trial_id;
  document.getElementById("detail-summary").textContent =
    `${row.decision}; conflict review: ${row.adjudication.status}. Model: ${row.model}. ` +
    `Rule origin: ${row.scanner_evidence.rule_origins.join(", ")}.`;
  const sections = document.getElementById("detail-sections");
  sections.replaceChildren();
  const material = row.review_material;
  const fields = [
    ["Candidate patch", material.patch],
    ["Original source", material.baseline_source],
    ["Candidate source", material.candidate_source],
    ["Scanner rules and candidate findings", { target_rules: material.target_rule_ids, findings: material.candidate_findings }],
    ["Security observations", material.security_tests],
    ["Functional observations", material.functional_tests],
    ["Decision evidence", row.evidence],
    ["Human review record", row.adjudication],
    ["Bound artifact paths and hashes", row.artifacts],
  ];
  for (const [title, value] of fields) {
    const details = node("details");
    details.append(node("summary", title));
    const pre = node("pre");
    pre.append(node("code", typeof value === "string" ? value : JSON.stringify(value, null, 2)));
    details.append(pre);
    sections.append(details);
  }
  sections.firstElementChild.open = true;
  document.getElementById("primary-detail").scrollIntoView({ behavior: "smooth", block: "start" });
}

async function loadPrimary() {
  try {
    const response = await fetch("/data/evaluation/primary-report.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`Primary report unavailable (${response.status}). Generate the verified primary report first.`);
    const report = await response.json();
    if (report.artifact_type !== "verified_primary_report" || report.evidence_verified !== true) {
      throw new Error("Expected a verified primary report.");
    }
    const metrics = report.metrics;
    const cards = [
      ["Initial attempts", report.attempt_count],
      ["Ready for human review", metrics.fixproof_disposition_distribution.READY_FOR_HUMAN_REVIEW || 0],
      ["SAST/runtime disagreements", metrics.sast_runtime_disagreement.count],
      ["Observed SAST false successes", metrics.sast_false_success.count],
    ];
    const grid = document.getElementById("primary-metrics");
    for (const [label, value] of cards) {
      const card = node("article", undefined, "panel");
      card.append(node("p", label, "section-kicker"), node("h2", value));
      grid.append(card);
    }
    const review = report.adjudication_summary;
    document.getElementById("primary-reviews").textContent =
      `Conflict reviews completed: ${review.completed}/${review.required}. ` +
      `Pending packets: ${review.pending}; missing packets: ${review.missing_packet}. Ready for review is not human approval.`;
    document.getElementById("primary-interpretation").textContent =
      `SAST-only apparent success: ${metrics.sast_only_apparent_success.count}/${report.attempt_count}. ` +
      `Security checks pass: ${metrics.targeted_security_pass.count}/${report.attempt_count}; ` +
      `functional checks pass: ${metrics.functional_preservation.count}/${report.attempt_count}. ` +
      "Pilot attempts and the constructed non-AI control are excluded.";
    const body = document.getElementById("primary-rows");
    for (const row of report.experiment_matrix) {
      const tr = node("tr");
      const cell = node("td");
      const button = node("button", `${row.case} ${row.attempt}`);
      button.type = "button";
      button.addEventListener("click", () => showTrial(row));
      cell.append(button);
      tr.append(cell);
      const evidence = row.evidence;
      for (const value of [row.cwe, evidence.target_sast,
        `${evidence.security.passed}/${evidence.security.total}`,
        `${evidence.functional.passed}/${evidence.functional.total}`,
        row.decision, row.adjudication.status]) tr.append(node("td", value));
      body.append(tr);
    }
    for (const limit of report.limitations) document.getElementById("primary-limits").append(node("li", limit));
    document.getElementById("primary-status").textContent = "Verified recorded evidence. This page does not rerun scans, models, or runtime tests.";
  } catch (error) {
    document.getElementById("primary-status").textContent = error.message;
  } finally {
    document.getElementById("primary-dashboard").setAttribute("aria-busy", "false");
  }
}

loadPrimary();
