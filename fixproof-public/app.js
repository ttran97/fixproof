"use strict";

const DATA_URL = "data/public-evidence.json";

const verdictLabels = {
  ACCEPT_CANDIDATE: "Accept candidate",
  REQUEST_ADDITIONAL_TESTING: "Request more testing",
  FOLLOW_UP_ACCEPT_CANDIDATE: "Bounded accept",
  FOLLOW_UP_REJECT_CANDIDATE: "Reject candidate",
  FOLLOW_UP_REQUEST_MORE_TESTING: "Request more testing",
  READY_FOR_HUMAN_REVIEW: "Ready for human review",
  NEEDS_HUMAN_ADJUDICATION: "Needs human adjudication",
  REJECT: "Reject"
};

let evidence = null;

function el(tag, className = "", text = "") {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== "") node.textContent = text;
  return node;
}

function label(value) {
  if (!value) return "No recorded result";
  return verdictLabels[value] || value.toLowerCase().replaceAll("_", " ");
}

function badge(value, text = label(value)) {
  const normalized = String(value || "").toLowerCase();
  let kind = "neutral";
  if (normalized.includes("accept") || normalized === "resolved" || normalized === "pass") kind = "pass";
  if (normalized.includes("reject") || normalized === "fail") kind = "fail";
  if (normalized.includes("request") || normalized.includes("inconclusive")) kind = "request";
  if (normalized.includes("review") || normalized.includes("adjudication")) kind = "review";
  return el("span", `badge ${kind}`, text);
}

function ratio(record) {
  return `${record.passed}/${record.total}`;
}

function pfi(record) {
  return `${record.pass}/${record.fail}/${record.inconclusive}`;
}

function addCell(row, content) {
  const cell = el("td");
  if (content instanceof Node) cell.append(content);
  else cell.textContent = String(content);
  row.append(cell);
  return cell;
}

function candidateName(candidate) {
  const wrapper = el("span", "candidate-name", candidate.id);
  wrapper.append(el("small", "", `${candidate.cwe} · ${candidate.case}`));
  return wrapper;
}

function reviewVerdict(review) {
  return review ? badge(review.verdict) : badge("", "No human result");
}

function evidenceButton(candidate) {
  const button = el("button", "evidence-button", "View evidence");
  button.type = "button";
  button.dataset.candidate = candidate.trial_id;
  button.addEventListener("click", () => openCandidate(candidate));
  return button;
}

function filteredCandidates() {
  const family = document.getElementById("case-filter").value;
  const query = document.getElementById("candidate-search").value.trim().toLowerCase();
  return evidence.candidates.filter((candidate) => {
    if (family !== "all" && candidate.case_id !== family) return false;
    if (!query) return true;
    const searchable = [
      candidate.id,
      candidate.case,
      candidate.cwe,
      candidate.trial_id,
      candidate.primary.original_human?.rationale,
      candidate.supplemental.later_human?.rationale,
      ...candidate.supplemental.nonpassing.map((item) => `${item.test_id} ${item.reason}`)
    ].filter(Boolean).join(" ").toLowerCase();
    return searchable.includes(query);
  });
}

function renderTables() {
  const candidates = filteredCandidates();
  const primaryBody = document.getElementById("primary-body");
  const supplementalBody = document.getElementById("supplemental-body");
  primaryBody.replaceChildren();
  supplementalBody.replaceChildren();

  if (!candidates.length) {
    const primaryEmpty = el("tr");
    const primaryCell = el("td", "empty-row", "No candidates match this filter.");
    primaryCell.colSpan = 8;
    primaryEmpty.append(primaryCell);
    primaryBody.append(primaryEmpty);

    const supplementalEmpty = el("tr");
    const supplementalCell = el("td", "empty-row", "No candidates match this filter.");
    supplementalCell.colSpan = 7;
    supplementalEmpty.append(supplementalCell);
    supplementalBody.append(supplementalEmpty);
    return;
  }

  for (const candidate of candidates) {
    const primaryRow = el("tr");
    addCell(primaryRow, candidateName(candidate));
    addCell(primaryRow, badge(candidate.primary.target_sast));
    addCell(primaryRow, ratio(candidate.primary.security));
    addCell(primaryRow, ratio(candidate.primary.functional));
    addCell(primaryRow, badge(candidate.primary.automated_decision));
    addCell(primaryRow, reviewVerdict(candidate.primary.original_human));
    addCell(primaryRow, reviewVerdict(candidate.supplemental.later_human));
    addCell(primaryRow, evidenceButton(candidate));
    primaryBody.append(primaryRow);

    const supplementalRow = el("tr");
    addCell(supplementalRow, candidateName(candidate));
    addCell(supplementalRow, pfi(candidate.supplemental.security));
    addCell(supplementalRow, pfi(candidate.supplemental.parity));
    addCell(supplementalRow, pfi(candidate.supplemental.robustness));
    const nonpassing = candidate.supplemental.nonpassing.length
      ? candidate.supplemental.nonpassing.map((item) => `${item.test_id} (${item.status})`).join(", ")
      : "None in registered supplement";
    addCell(supplementalRow, nonpassing);
    addCell(supplementalRow, reviewVerdict(candidate.supplemental.later_human));
    addCell(supplementalRow, evidenceButton(candidate));
    supplementalBody.append(supplementalRow);
  }
}

function metric(value, description, tone) {
  const card = el("article", `metric-card ${tone}`);
  card.append(el("strong", "", value), el("span", "", description));
  return card;
}

function renderSummary() {
  const primary = evidence.primary_summary;
  const supplemental = evidence.supplemental_summary;
  const grid = document.getElementById("metric-grid");
  grid.replaceChildren(
    metric(String(primary.attempts), "frozen primary candidates", "blue"),
    metric(`${primary.target_sast_resolved}/15`, "target SAST findings resolved", "gold"),
    metric(String(supplemental.candidate_case_observations.total), "supplemental candidate-case observations", "green"),
    metric(String(supplemental.later_human_records), "later human records", "purple")
  );
  document.getElementById("recording-note").textContent = evidence.scope.recording_note;
  document.getElementById("data-date").textContent = `Evidence cutoff: ${evidence.evidence_cutoff.slice(0, 10)} · Public export: ${evidence.generated_on.slice(0, 10)}`;

  const limitations = document.getElementById("limitations");
  limitations.replaceChildren(...evidence.limitations.map((item) => el("li", "", item)));
}

function definitionList(items) {
  const list = el("dl");
  for (const [term, value] of items) {
    list.append(el("dt", "", term), el("dd", "", value));
  }
  return list;
}

function reviewCard(title, review, emptyText) {
  const card = el("section", "review-card");
  card.append(el("h3", "", title));
  if (!review) {
    card.append(el("p", "review-meta", emptyText));
    return card;
  }
  card.append(el("p", "review-meta", `${label(review.verdict)} · recorded ${review.reviewed_on}`));
  const quote = el("blockquote", "", review.rationale);
  card.append(quote);
  return card;
}

function openCandidate(candidate) {
  const dialog = document.getElementById("candidate-dialog");
  document.getElementById("dialog-title").textContent = candidate.id;
  document.getElementById("dialog-subtitle").textContent = `${candidate.case} · ${candidate.cwe} · saved candidate ${candidate.attempt}`;

  const content = document.getElementById("dialog-content");
  content.replaceChildren();

  const summary = el("div", "detail-grid");
  const primaryCard = el("section", "detail-card");
  primaryCard.append(
    el("h3", "", "Frozen primary-v1"),
    definitionList([
      ["Target SAST", candidate.primary.target_sast],
      ["Security suite", ratio(candidate.primary.security)],
      ["Functional suite", ratio(candidate.primary.functional)],
      ["Automated state", label(candidate.primary.automated_decision)]
    ])
  );

  const supplementalCard = el("section", "detail-card");
  supplementalCard.append(
    el("h3", "", "Supplemental-v1"),
    definitionList([
      ["All registered", `${candidate.supplemental.pass}/${candidate.supplemental.registered} pass`],
      ["Security P/F/I", pfi(candidate.supplemental.security)],
      ["Parity P/F/I", pfi(candidate.supplemental.parity)],
      ["Robustness P/F/I", pfi(candidate.supplemental.robustness)]
    ])
  );

  const boundaryCard = el("section", "detail-card");
  boundaryCard.append(
    el("h3", "", "Record boundary"),
    definitionList([
      ["Original review", candidate.primary.original_human ? label(candidate.primary.original_human.verdict) : "No original human result"],
      ["Later follow-up", candidate.supplemental.later_human ? label(candidate.supplemental.later_human.verdict) : "No later follow-up"],
      ["Primary overwritten", "No"]
    ])
  );
  summary.append(primaryCard, supplementalCard, boundaryCard);
  content.append(summary);

  const nonpassingSection = el("section", "detail-card");
  nonpassingSection.append(el("h3", "", "Nonpassing supplemental cases"));
  if (!candidate.supplemental.nonpassing.length) {
    nonpassingSection.append(el("p", "", "None in the registered supplemental cases for this candidate."));
  } else {
    const list = el("ul", "case-list");
    for (const item of candidate.supplemental.nonpassing) {
      const entry = el("li");
      entry.append(el("strong", "", `${item.test_id} · ${item.status}`), el("p", "", `${item.category}: ${item.reason}`));
      list.append(entry);
    }
    nonpassingSection.append(list);
  }
  content.append(nonpassingSection);

  content.append(
    reviewCard("Original human decision", candidate.primary.original_human, "No original primary human decision was recorded."),
    reviewCard("Later human follow-up", candidate.supplemental.later_human, "No later follow-up decision was recorded for this candidate.")
  );

  const patchCard = el("section", "detail-card");
  patchCard.append(el("h3", "", "Candidate patch excerpt"));
  const pre = el("pre");
  pre.append(el("code", "", candidate.patch_excerpt || "No changed-line excerpt available."));
  patchCard.append(pre);
  content.append(patchCard);

  dialog.showModal();
}

async function initialize() {
  try {
    const response = await fetch(DATA_URL, { cache: "no-store" });
    if (!response.ok) throw new Error(`Evidence request returned HTTP ${response.status}`);
    evidence = await response.json();
    renderSummary();
    renderTables();
  } catch (error) {
    const message = document.getElementById("load-error");
    message.hidden = false;
    message.textContent = `The saved evidence could not be loaded: ${error.message}. Serve or deploy the complete fixproof-public folder instead of opening index.html alone.`;
  }
}

document.getElementById("case-filter").addEventListener("change", renderTables);
document.getElementById("candidate-search").addEventListener("input", renderTables);
document.getElementById("dialog-close").addEventListener("click", () => document.getElementById("candidate-dialog").close());
document.getElementById("candidate-dialog").addEventListener("click", (event) => {
  if (event.target === event.currentTarget) event.currentTarget.close();
});

initialize();
