# Remaining candidate follow-up review worksheet (draft)

Prepared September 22, 2026 for Progress Report 3 preparation. Tony confirmed
that he reviewed this evidence. Nine decisions from this worksheet are now
stored as separate dated supplemental human records: SQLi 01–05 are bounded
acceptances, and Traversal 02–05 request more testing. XSS 03 remains without a
separate later record because its original bounded acceptance is consistent
with all nine passing supplemental cases. No primary-v1 record, registered test
outcome, or primary metric was changed.

The [primary report](../../../data/evaluation/primary-report.json) and
[supplemental report](../../../data/supplemental/v1/supplemental-report.json)
were verified against their saved evidence on September 22. Five SQLi attempts
produced one identical candidate source, but remain five separate attempts and
five separate result records. The supplemental run made no new model calls or
primary SAST scans.

## Decision boundary to settle before signing

- A **primary SAST resolution** or `READY_FOR_HUMAN_REVIEW` is not a human
  approval. A supplemental security pass does not erase a parity or robustness
  failure.
- `SQL-R01`, `PATH-R01`, `PATH-R02`, and `PATH-R03` are new, pre-registered
  robustness contracts. They are not retroactive primary security failures.
  Tony stated on September 22 that a low-severity robustness failure need not
  block bounded acceptance when code inspection and recorded outcomes show no
  harmful security or parity effect. This is a *decision criterion*, not a
  retest: every failed case stays recorded as `fail`. A wrong status code can
  still affect clients, so each rationale must explain the observed impact and
  explicitly qualify any acceptance. Three failures in Traversal 03 merit
  separate scrutiny rather than automatic grouping with a single failure.
- `PATH-S06` is **inconclusive**, because the Windows symlink fixture could not
  be created. A lexical `path.resolve` containment check does not itself check
  the target of a symlink; that is a code-level concern, not an observed
  `PATH-S06` failure. Do not report symlink protection as passed. Tony chose
  **request more testing** as the stated direction for Traversal 02 and 04
  until a symlink-capable check can resolve this uncertainty. The same
  inconclusive case also limits Traversal 03 and 05; absent another reason to
  reject them, they likewise should not receive an unqualified later acceptance.
- The original reviews and primary metrics remain frozen. Any new decision
  would be a separately dated qualification. The current formal follow-up
  recorder is limited to the five previously reviewed targets; additional
  formal records need a deliberate workflow extension and Tony's approval.

## Tony's stated review direction

Tony provided the following interpretation on September 22, 2026. These are
the directions to use when preparing the candidate-specific human records;
they do not become signed evidence until Tony completes the checklist below.

| Candidate | Direction for Tony to assess | Why no final verdict is recorded yet |
| --- | --- | --- |
| XSS 03 | Reaffirm bounded acceptance | Tony has not confirmed this later judgment |
| SQLi 01–05 | Accept for the bounded SQL-injection repair | All registered security and parity cases passed; retain `SQL-R01` as a documented low-impact robustness failure |
| Traversal 02, 04 | Request more testing | Tony chose to keep the unexecuted symlink security case unresolved |
| Traversal 03 | Request more testing | Three malformed-input contracts failed, and symlink security is unresolved |
| Traversal 05 | Request more testing, with one robustness failure disclosed | Symlink security is unresolved even if the HTTP 404/400 difference is judged low impact |

"Qualified acceptance" above would be a human disposition, **not** a change
to any registered case's `fail` or `inconclusive` outcome.

## Patch excerpts to show if asked

These are short excerpts of the saved candidate patches, not newly proposed
changes. Open the complete patch before judging its context.

**XSS 03:** [patch](../../../data/primary_trials/v1/cases/xss/attempt-03/workspace/CF-209ae17232b1/attempt-03/candidate.patch). The crucial expression is `String(value)` inside `escapeHtml`, followed by entity replacements and `res.send("<h1>Hello " + escapeHtml(name) + "</h1>")`. Unlike the rejected XSS candidates' nullish-to-empty conversion, `String(undefined)` preserves the frozen missing-name text.

**SQLi 01–05:** representative [patch 01](../../../data/primary_trials/v1/cases/sqli/attempt-01/workspace/CF-8b662341cc2d/attempt-01/candidate.patch). All five candidate sources are identical:

```js
const username = req.query.username;
const query = "SELECT id, username, role FROM users WHERE username = ?";
db.all(query, [username], (err, rows) => { /* response handling */ });
```

The placeholder separates input from SQL syntax in the registered attacks.
The route has no preceding scalar-type check for duplicate `username` values.
For `username=alice&username=bob`, every saved candidate returned HTTP 200
with `[]`; the new contract required HTTP 400 with a stable JSON error.

**Traversal 02/04:** [patch 02](../../../data/primary_trials/v1/cases/path-traversal/attempt-02/workspace/CF-17216aac7b7a/attempt-02/candidate.patch), [patch 04](../../../data/primary_trials/v1/cases/path-traversal/attempt-04/workspace/CF-17216aac7b7a/attempt-04/candidate.patch). Both reject an empty or nonscalar `name`, then compare a lexically resolved path to the resolved root plus `path.sep`:

```js
if (typeof name !== "string" || name.length === 0) { /* HTTP 400 */ }
const rootPath = path.resolve(fileRoot);
const filePath = path.resolve(rootPath, name);
if (filePath !== rootPath && !filePath.startsWith(rootPath + path.sep)) {
    /* HTTP 400 */
}
```

**Traversal 03:** [patch](../../../data/primary_trials/v1/cases/path-traversal/attempt-03/workspace/CF-17216aac7b7a/attempt-03/candidate.patch). `path.resolve(rootPath, String(name || ""))` supplies no explicit missing/empty/nonscalar rejection. In the recorded run, missing, empty, and repeated values returned HTTP 404 rather than the registered HTTP 400.

**Traversal 05:** [patch](../../../data/primary_trials/v1/cases/path-traversal/attempt-05/workspace/CF-17216aac7b7a/attempt-05/candidate.patch). `path.resolve(fileRoot, String(name || ""))` and a `rootPath + path.sep` prefix check returned HTTP 400 for missing and empty names, but the repeated-name case returned HTTP 404 instead of the registered HTTP 400.

## Candidate-by-candidate draft rationales

These paragraphs document the evidence used for Tony's decisions. The formal
SQLi and Traversal result files contain the recorded rationales; XSS 03 remains
an explanatory draft because no separate later decision was needed.

### XSS 03 — provisional direction: reaffirm bounded acceptance

[Original review](../../../data/primary_reviews/v1/primary-v1-xss-initial-03/result.json) · [supplemental result](../../../data/supplemental/v1/runs/20260914T192749827554Z-candidates-xss/attempt-03/result.json)

The saved patch converts `name` with `String(name)` and escapes HTML-sensitive
characters before writing into the `/hello` element-content sink. The primary
review accepted it for that bounded context despite persistent SAST findings.
The supplement passed all 3 security, 5 behavioral-parity, and 1 robustness
case. In particular, omitted `name` retained `Hello undefined`, unlike XSS
01/02/04/05. No registered supplemental result presently calls for reversing
the original bounded acceptance. This is not proof that the helper is safe in
other HTML contexts or against unregistered inputs.

### SQLi 01 — Tony's direction: bounded acceptance

[Primary decision](../../../data/primary_trials/v1/cases/sqli/attempt-01/decision.json) · [supplemental result](../../../data/supplemental/v1/runs/20260914T192901912061Z-candidates-sqli/attempt-01/result.json)

The candidate replaced SQL string concatenation with a parameterized lookup.
The target SAST finding resolved, the primary security and functional checks
passed, and the automated state was ready for human review—not human approval.
The supplement passed 3/3 security and 2/2 parity cases, plus 2/3 robustness
cases. `SQL-R01` sent two `username` parameters and observed HTTP 200 `[]`
instead of the registered HTTP 400 JSON error. This is a new input-contract
failure, not observed SQL injection. HTTP 200 can mislead clients expecting a
rejected ambiguous request, but the saved response returned no user row. Tony
judges this response difference as non-severe for the bounded repair
because no user row or broadened result was returned. The candidate can be
accepted for the tested SQL-injection repair with this explicit limitation;
`SQL-R01` must still be reported as failed.

### SQLi 02 — Tony's direction: bounded acceptance

[Primary decision](../../../data/primary_trials/v1/cases/sqli/attempt-02/decision.json) · [supplemental result](../../../data/supplemental/v1/runs/20260914T192901912061Z-candidates-sqli/attempt-02/result.json)

This attempt has the same saved parameterized-query source as SQLi 01, but its
own recorded primary and supplemental outcomes. The target SAST finding
resolved and the original 2/2 security and 3/3 functional checks passed; no
human acceptance was recorded. Supplemental security was 3/3, parity 2/2,
and robustness 2/3. For `SQL-R01`, duplicate `username` parameters produced
HTTP 200 `[]` instead of required HTTP 400. This is failure of the new
robustness contract, not a demonstrated bypass of the parameterized query.
The no-row response limits observed security impact, although HTTP 200 may
mislead an API client. Tony accepts the bounded SQL-injection repair with that
limitation stated; the registered `SQL-R01` failure does not become a pass.

### SQLi 03 — Tony's direction: bounded acceptance

[Primary decision](../../../data/primary_trials/v1/cases/sqli/attempt-03/decision.json) · [supplemental result](../../../data/supplemental/v1/runs/20260914T192901912061Z-candidates-sqli/attempt-03/result.json)

The saved source again uses `WHERE username = ?` with `[username]`, and the
primary target SAST and runtime checks reached ready-for-review status without
a human verdict. The supplemental result passed all three attack cases, both
parity cases, and two of three robustness cases. `SQL-R01` failed because the
ambiguous repeated value returned HTTP 200 `[]` rather than HTTP 400. Any
later interpretation must be based on the new robustness criterion, not on a
claim that the registered SQL attacks succeeded. Tony accepts the bounded
repair because the tested attacks returned no unauthorized rows, while naming
the incorrect HTTP status as a client-visible limitation and keeping
`SQL-R01` failed.

### SQLi 04 — Tony's direction: bounded acceptance

[Primary decision](../../../data/primary_trials/v1/cases/sqli/attempt-04/decision.json) · [supplemental result](../../../data/supplemental/v1/runs/20260914T192901912061Z-candidates-sqli/attempt-04/result.json)

The source and patch are the same as the other four SQLi attempts. This
attempt separately resolved the target SAST finding and passed the fixed
primary tests, leaving it ready for human review. Its eight registered
supplemental cases yielded seven passes and one failure: `SQL-R01` observed
HTTP 200 `[]` for repeated usernames where HTTP 400 was required. The
security and baseline-parity cases passed; the missing scalar-input check is
a newly registered robustness limitation. The response returned no row, but
HTTP 200 can conceal ambiguity from a caller. Tony accepts the bounded tested
repair while retaining and disclosing the failed robustness result.

### SQLi 05 — Tony's direction: bounded acceptance

[Primary decision](../../../data/primary_trials/v1/cases/sqli/attempt-05/decision.json) · [supplemental result](../../../data/supplemental/v1/runs/20260914T192901912061Z-candidates-sqli/attempt-05/result.json)

The same parameterized candidate source again removed the primary target
finding and passed the original security and functional suites, but no human
approval exists. The supplement passed 3/3 security, 2/2 parity, and 2/3
robustness cases. `SQL-R01` returned HTTP 200 `[]` for two `username`
parameters rather than the required HTTP 400 JSON error. This limits claims
about ambiguous-input handling, while not demonstrating SQL injection in the
registered attacks. A formal later verdict must state how the new contract
affects acceptance. Under Tony's low-severity criterion, the no-row response
supports bounded acceptance for the tested security repair, while the wrong
HTTP status remains a documented failure.

### Traversal 02 — Tony's direction: request more testing

[Original review](../../../data/primary_reviews/v1/primary-v1-path-traversal-initial-02/result.json) · [supplemental result](../../../data/supplemental/v1/runs/20260914T192827434537Z-candidates-path-traversal/attempt-02/result.json)

The original review accepted this patch within the controlled `/file` scope.
Its typed-input guard and lexical root-boundary check passed both supplemental
parity, all three robustness, and five executable security cases. `PATH-S06`
was inconclusive because the link fixture could not be created. The code does
not visibly check the resolved filesystem target before `fs.readFile`, so the
unexecuted symlink scenario cannot be claimed safe from this evidence. The
original bounded acceptance can remain historical; a broader security claim
should await an environment-capable `PATH-S06` run or another explicit review.

### Traversal 03 — Tony's direction: request more testing

[Original review](../../../data/primary_reviews/v1/primary-v1-path-traversal-initial-03/result.json) · [supplemental result](../../../data/supplemental/v1/runs/20260914T192827434537Z-candidates-path-traversal/attempt-03/result.json)

The original bounded acceptance was based on the fixed primary attack and
functional checks. The supplement passed five executable security and both
parity cases, but `PATH-R01`, `PATH-R02`, and `PATH-R03` all returned HTTP 404
instead of the required HTTP 400. The `String(name || "")` conversion does not
reject missing, empty, or repeated input before path resolution. `PATH-S06`
remains inconclusive. These are three new robustness-contract failures, not
observed traversal security failures. Tony treats the HTTP-status differences
as robustness limitations rather than
observed traversal attacks, but three malformed-input classes failed and the
symlink case is unresolved. The later direction is therefore request more
testing, not acceptance or a claim of complete traversal protection.

### Traversal 04 — Tony's direction: request more testing

[Original review](../../../data/primary_reviews/v1/primary-v1-path-traversal-initial-04/result.json) · [supplemental result](../../../data/supplemental/v1/runs/20260914T192827434537Z-candidates-path-traversal/attempt-04/result.json)

The patch validates that `name` is a nonempty string and enforces a lexical
root-plus-separator boundary. It passed both supplemental parity cases, all
three robustness cases, and all five executable security cases. The sixth
security case, `PATH-S06`, could not execute, so its outcome is inconclusive.
No registered failure presently reverses the original bounded acceptance,
but the lexical check does not itself validate a symlink target. A claim of
symlink-safe traversal prevention needs a separate executable test or review.

### Traversal 05 — Tony's direction: request more testing

[Original review](../../../data/primary_reviews/v1/primary-v1-path-traversal-initial-05/result.json) · [supplemental result](../../../data/supplemental/v1/runs/20260914T192827434537Z-candidates-path-traversal/attempt-05/result.json)

The primary review accepted this patch for the fixed `/file` fixture and noted
that unusual query values needed more testing. The supplement passed five
executable security, both parity, and two robustness cases. `PATH-R03` sent
two `name` parameters and returned HTTP 404 instead of the registered HTTP
400. The patch converts `name` with `String(name || "")`, with no explicit
nonscalar-input rejection. `PATH-S06` remains inconclusive. This is one new
robustness-contract failure, not an observed traversal attack. If the contract
is acceptance-blocking, a later rejection would be consistent. Under Tony's
low-severity rule, this robustness failure alone need not force rejection
because the malformed request disclosed no outside content, but HTTP 404
instead of 400 is still a client-visible contract failure. Do not claim full
supplemental conformance or symlink safety. Consistent with Tony's criterion for
Traversal 02/04, the stated later direction is request more testing until
`PATH-S06` can run.

## Tony's review checklist

For each candidate, inspect the full saved patch, original decision/review,
and every case in the linked supplemental result; check the raw response and
oracle reason rather than relying only on the summary. Compare candidates
within the same CWE. Then write Tony's own verdict and rationale, with a date,
explicitly distinguishing security, parity, robustness, and inconclusive
outcomes. Do not alter the original acceptance records or primary metrics. If
any wording above does not match Tony's judgment, revise it before recording.
