"use strict";

const CASE_HEADERS = [
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
];

const SUMMARY_HEADERS = [
  "Candidate",
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
];

const COUNT_HEADERS = [
  "Evidence layer",
  "Unit/category",
  "Denominator",
  "Pass/resolved",
  "Fail/persistent",
  "Inconclusive",
  "Meaning",
];

const DECISION_HEADERS = [
  "Candidate",
  "Evidence layer",
  "Reviewed on",
  "Verdict",
  "Rationale",
  "Relationship/notes",
  "Source evidence",
];

let allCases = [];
let currentPage = 1;

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = String(text);
  return node;
}

function appendTextCell(row, value, className = "") {
  const cell = element("td", className, value || "—");
  row.appendChild(cell);
  return cell;
}

function badge(value) {
  const normalized = String(value || "").toLowerCase();
  let kind = "neutral";
  if (normalized === "pass" || normalized === "resolved" || normalized.includes("accept_candidate")) kind = "pass";
  if (normalized === "fail" || normalized === "persistent" || normalized.includes("reject_candidate")) kind = "fail";
  if (normalized === "inconclusive" || normalized.includes("request_more_testing")) kind = "request";
  return element("span", "badge " + kind, value || "Not recorded");
}

function appendDetailsCell(row, summary, value, extra = "") {
  const cell = element("td", extra);
  if (!value) {
    cell.textContent = "—";
  } else {
    const details = document.createElement("details");
    details.appendChild(element("summary", "", summary));
    details.appendChild(element("pre", "cell-output", value));
    cell.appendChild(details);
  }
  row.appendChild(cell);
  return cell;
}

function renderHeader(targetId, headers) {
  const target = document.getElementById(targetId);
  const row = document.createElement("tr");
  headers.forEach((header) => row.appendChild(element("th", "", header)));
  target.replaceChildren(row);
}

function renderMetrics(data) {
  const metrics = [
    ["15", "saved repair candidates", "blue"],
    [String(data.primary_cases.length), "primary runtime observations", "green"],
    [String(data.supplemental_cases.length), "frozen supplemental-v1 observations", "purple"],
    [String(data.path_s06_extension.length), "separate PATH-S06 observations", "red"],
    [String(data.human_decisions.length), "human decision records across layers", "gold"],
  ];
  const container = document.getElementById("evidence-metrics");
  container.replaceChildren();
  metrics.forEach(([value, label, color]) => {
    const card = element("article", "metric-card " + color);
    card.appendChild(element("strong", "", value));
    card.appendChild(element("span", "", label));
    container.appendChild(card);
  });
}

function renderCandidateSummary(rows) {
  renderHeader("candidate-head", SUMMARY_HEADERS);
  const body = document.getElementById("candidate-body");
  body.replaceChildren();
  rows.forEach((item) => {
    const row = document.createElement("tr");
    SUMMARY_HEADERS.forEach((header) => {
      const cell = document.createElement("td");
      const value = item[header] || "—";
      if (["Target SAST", "Original human", "Supplemental later human", "PATH-S06 later human"].includes(header)) {
        cell.appendChild(badge(value));
      } else {
        cell.textContent = value;
      }
      row.appendChild(cell);
    });
    body.appendChild(row);
  });
}

function caseSearchText(item) {
  return CASE_HEADERS.map((header) => item[header] || "").join(" ").toLowerCase();
}

function renderCases() {
  const layer = document.getElementById("layer-filter").value;
  const candidate = document.getElementById("candidate-filter").value;
  const result = document.getElementById("result-filter").value;
  const search = document.getElementById("case-search").value.trim().toLowerCase();

  const filtered = allCases.filter((item) => {
    if (layer !== "all" && item["Evidence layer"] !== layer) return false;
    if (candidate !== "all" && item.Candidate !== candidate) return false;
    if (result !== "all" && item.Result !== result) return false;
    return !search || caseSearchText(item).includes(search);
  });

  const sizeValue = document.getElementById("page-size").value;
  const pageSize = sizeValue === "all" ? Math.max(filtered.length, 1) : Number(sizeValue);
  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  currentPage = Math.min(currentPage, totalPages);
  const start = (currentPage - 1) * pageSize;
  const visible = filtered.slice(start, start + pageSize);
  const firstShown = filtered.length ? start + 1 : 0;
  const lastShown = filtered.length ? start + visible.length : 0;

  document.getElementById("case-result-count").textContent =
    "Showing " + firstShown + "–" + lastShown + " of " + filtered.length +
    " matching rows (" + allCases.length + " total).";
  document.getElementById("page-status").textContent =
    "Page " + currentPage + " of " + totalPages;
  document.getElementById("previous-page").disabled = currentPage <= 1;
  document.getElementById("next-page").disabled = currentPage >= totalPages;

  const body = document.getElementById("case-body");
  body.replaceChildren();
  if (!visible.length) {
    const row = document.createElement("tr");
    const cell = element("td", "empty-row", "No evidence rows match these filters.");
    cell.colSpan = 10;
    row.appendChild(cell);
    body.appendChild(row);
    return;
  }

  visible.forEach((item) => {
    const row = document.createElement("tr");
    appendTextCell(row, item.Candidate, "candidate-name");
    appendTextCell(row, item["Evidence layer"] + "\n" + item.Category);
    appendTextCell(row, item["Case/Test ID"] + "\n" + item.CWE);
    appendTextCell(row, item["Input/Payload"], "payload-cell");
    appendTextCell(row, item["Effective request(s)"], "request-cell");
    appendDetailsCell(row, "View expected contract", item["Expected result/contract"]);
    appendTextCell(row, item["Observed HTTP status(es)"]);

    const outputParts = [item["Observed response/output"]];
    if (item["Browser/secondary observation"]) {
      outputParts.push("Secondary observation:\n" + item["Browser/secondary observation"]);
    }
    appendDetailsCell(row, "View recorded output", outputParts.filter(Boolean).join("\n\n"));

    const resultCell = document.createElement("td");
    resultCell.appendChild(badge(item.Result));
    resultCell.appendChild(element("p", "case-reason", item["Evaluation reason"]));
    row.appendChild(resultCell);

    appendTextCell(row, item["Source evidence"], "source-cell");
    body.appendChild(row);
  });
}

function resetAndRenderCases() {
  currentPage = 1;
  renderCases();
}

function populateCandidateFilter(rows) {
  const select = document.getElementById("candidate-filter");
  [...new Set(rows.map((row) => row.Candidate))].forEach((candidate) => {
    const option = element("option", "", candidate);
    option.value = candidate;
    select.appendChild(option);
  });
}

function renderSimpleTable(headId, bodyId, headers, rows, badgeHeader = "") {
  renderHeader(headId, headers);
  const body = document.getElementById(bodyId);
  body.replaceChildren();
  rows.forEach((item) => {
    const row = document.createElement("tr");
    headers.forEach((header) => {
      const cell = document.createElement("td");
      const value = item[header] ?? "";
      if (header === badgeHeader) {
        cell.appendChild(badge(value));
      } else if (header === "Rationale") {
        const details = document.createElement("details");
        details.appendChild(element("summary", "", "Read rationale"));
        details.appendChild(element("p", "decision-rationale", value));
        cell.appendChild(details);
      } else {
        cell.textContent = value || "—";
      }
      row.appendChild(cell);
    });
    body.appendChild(row);
  });
}

async function loadEvidence() {
  const error = document.getElementById("evidence-load-error");
  try {
    const response = await fetch("data/student-test-evidence.json", { cache: "no-store" });
    if (!response.ok) throw new Error("Evidence request failed with HTTP " + response.status + ".");
    const data = await response.json();

    allCases = [
      ...data.primary_cases,
      ...data.supplemental_cases,
      ...data.path_s06_extension,
    ];
    if (data.candidate_summary.length !== 15 || allCases.length !== 245) {
      throw new Error("The evidence export has an unexpected candidate or case count.");
    }

    document.getElementById("count-note").textContent = data.count_note;
    document.getElementById("evidence-date").textContent =
      "Generated from recorded evidence: " + data.generated_on.slice(0, 10);

    renderMetrics(data);
    renderCandidateSummary(data.candidate_summary);
    populateCandidateFilter(data.candidate_summary);
    renderCases();
    renderSimpleTable(
      "count-head",
      "count-body",
      COUNT_HEADERS,
      data.count_reconciliation,
    );
    renderSimpleTable(
      "decision-head",
      "decision-body",
      DECISION_HEADERS,
      data.human_decisions,
      "Verdict",
    );

    ["layer-filter", "candidate-filter", "result-filter", "page-size"].forEach((id) => {
      document.getElementById(id).addEventListener("change", resetAndRenderCases);
    });
    document.getElementById("case-search").addEventListener("input", resetAndRenderCases);
    document.getElementById("previous-page").addEventListener("click", () => {
      if (currentPage > 1) {
        currentPage -= 1;
        renderCases();
      }
    });
    document.getElementById("next-page").addEventListener("click", () => {
      currentPage += 1;
      renderCases();
    });
  } catch (problem) {
    error.hidden = false;
    error.textContent = "The case-evidence report could not load: " + problem.message;
  }
}

loadEvidence();
