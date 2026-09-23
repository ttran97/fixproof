# XSS 01-02 supplemental review checklist

Prepared and completed September 21, 2026. This document summarizes Tony
Tran's personal follow-up review. The bound `result.json` files are the
canonical decision records. Neither they nor this summary alter the original
primary-v1 review records.

## Why a follow-up is needed

The original reviews accepted XSS attempts 01 and 02 using the evidence then
available. The later, frozen `supplemental-v1` protocol applied the same nine
cases to all five saved XSS candidates. Attempts 01 and 02 each passed eight
cases and failed `XSS-P01`, the same behavioral-parity case that supported the
follow-up rejection of attempts 04 and 05.

The original acceptance remains a historical primary-study result. A new
decision must be recorded as a dated supplemental qualification rather than by
editing either original `result.json` file or the primary metrics.

## Evidence summary

| Evidence | XSS 01 | XSS 02 |
| --- | --- | --- |
| Original human verdict | `ACCEPT_CANDIDATE` | `ACCEPT_CANDIDATE` |
| Original rationale | Escaping HTML-sensitive characters | Replacement map escapes `&<>"'` |
| Primary SAST target | Persistent | Persistent |
| Primary security tests | 4/4 pass | 4/4 pass |
| Primary functional tests | 6/6 pass | 6/6 pass |
| Supplemental security | 3/3 pass | 3/3 pass |
| Supplemental behavioral parity | 4/5 pass | 4/5 pass |
| Supplemental robustness | 1/1 pass | 1/1 pass |
| Nonpassing case | `XSS-P01` | `XSS-P01` |
| Observed missing-name text | `Hello ` | `Hello ` |
| Frozen baseline expectation | `Hello undefined` | `Hello undefined` |
| Automatic supplemental acceptance | `false` | `false` |

Both patches convert a missing query value with `name ?? ""` before escaping.
That conversion explains the shared parity failure. The registered attacks did
not execute, so this is a behavioral-parity finding, not evidence that the
tested XSS attacks remained exploitable.

## Files to inspect

- Original reviews:
  `data/primary_reviews/v1/primary-v1-xss-initial-01/result.json` and
  `data/primary_reviews/v1/primary-v1-xss-initial-02/result.json`.
- Candidate patches:
  `data/primary_trials/v1/cases/xss/attempt-01/workspace/CF-209ae17232b1/attempt-01/candidate.patch`
  and the corresponding `attempt-02` path.
- Supplemental observations:
  `data/supplemental/v1/runs/20260914T192749827554Z-candidates-xss/attempt-01/result.json`
  and the corresponding `attempt-02` result.
- Criterion: `XSS-P01` in `docs/supplemental-protocol-v1.md`.
- Comparison decisions: the XSS 04 and 05 records under
  `data/supplemental/v1/follow-up-reviews/`.

## Personal review checks

For each candidate, confirm that you personally:

- inspected the patch and the original acceptance rationale;
- inspected all nine supplemental outcomes, not only the summary counter;
- distinguished security passes from the behavioral-parity failure;
- applied the same frozen `XSS-P01` criterion used for attempts 04 and 05;
- understood that a follow-up decision does not rewrite primary-v1; and
- selected and justified one conclusion: accept, reject, or request more
  testing.

## Recorded decisions

### XSS 01

- Follow-up verdict: `FOLLOW_UP_REJECT_CANDIDATE`
- Review date: September 21, 2026
- Rationale: Tony reviewed the patch, original decision, and all nine
  supplemental outcomes. The candidate passed all three supplemental security
  cases and the robustness case. `XSS-P01` nevertheless observed
  `<h1>Hello </h1>` instead of the frozen baseline
  `<h1>Hello undefined</h1>` because `String(value ?? "")` converted the
  missing value to an empty string. The frozen protocol requires exact parity,
  so Tony rejected the candidate for the bounded benchmark. This does not mean
  the registered XSS attacks remained exploitable.
- Canonical result:
  `data/supplemental/v1/follow-up-reviews/primary-v1-xss-initial-01/result.json`

### XSS 02

- Follow-up verdict: `FOLLOW_UP_REJECT_CANDIDATE`
- Review date: September 21, 2026
- Rationale: Tony reviewed the patch, original decision, and all nine
  supplemental outcomes. The candidate passed all three supplemental security
  cases and the robustness case. `XSS-P01` nevertheless observed
  `<h1>Hello </h1>` instead of the frozen baseline
  `<h1>Hello undefined</h1>` because `String(name ?? "")` converted the
  missing value to an empty string. The frozen protocol requires exact parity,
  so Tony rejected the candidate for the bounded benchmark. This does not mean
  the registered XSS attacks remained exploitable.
- Canonical result:
  `data/supplemental/v1/follow-up-reviews/primary-v1-xss-initial-02/result.json`

## Consistency note

If the frozen baseline-preservation requirement remains authoritative, the
same `XSS-P01` failure that supported rejection of attempts 04 and 05 supports
follow-up rejection of attempts 01 and 02. A different outcome is possible
only if the rationale clearly identifies a material difference or explicitly
changes the decision criterion. Any changed criterion should be described as a
later interpretation, not silently substituted into the frozen protocol.
