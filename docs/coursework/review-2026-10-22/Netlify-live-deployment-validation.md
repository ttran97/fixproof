# FixProof live Netlify deployment validation

Validated October 22, 2026 against <https://fixproof.netlify.app/>.

## Result

The October 21 version-2 PATH-S06 package is live. The deployed data files and
downloadable artifacts matched the corresponding local release files by
SHA-256. A headless Chromium run also exercised the rendered dashboard,
candidate details, filters, pagination, and test-evidence page.

## Direct publication checks

- The home page returned HTTP 200 and identified the separate PATH-S06
  extension.
- `/test-evidence` returned HTTP 200 and displayed the 245-observation evidence
  boundary: 100 primary-v1 cases, 140 supplemental-v1 cases, and five separate
  PATH-S06 extension cases.
- `data/public-evidence.json` reported 15 primary attempts, 140 supplemental-v1
  observations, five PATH-S06 failures, and five extension human
  qualifications.
- The workbook, evidence appendix, workflow image, and student-evidence JSON
  each returned HTTP 200 with the expected content type and byte length.

## Deployed artifact comparison

| Artifact | Bytes | SHA-256 | Matches local release |
| --- | ---: | --- | --- |
| `data/public-evidence.json` | 59,585 | `267B69F2D926A46EE0E40746E18E560706B9A2F083F5EF75486B584D1E495E17` | Yes |
| `data/student-test-evidence.json` | 267,909 | `718AC12E4F997805EFDE2233650355E18881103EAFF56F0C474F893518A52ADC` | Yes |
| `FixProof-15-candidate-test-evidence.xlsx` | 39,311 | `0AAE5F1C6FF4FDC21460A771D65937596F2E700DDB55B26E69C00431ED00752F` | Yes |
| `Video-III-15-candidate-evidence-appendix.pdf` | 151,909 | `B68EB826A011B56692519302AB9BAC9D11E886F02B40B7C4A1B942D64E743A58` | Yes |
| `assets/fixproof-workflow.png` | 136,586 | `9BCD3E5E6B08444CCF35D11283FF4EFCA292B48BF17EA2A0DF6E01FAAEE5F509` | Yes |

## Browser validation

The existing Playwright validator was run against the HTTPS deployment. It
confirmed:

- 15 primary rows and 15 supplemental rows;
- 10 original reviews, 14 supplemental-v1 human records, and five PATH-S06
  qualifications;
- Traversal 02's HTTP 200 marker disclosure, manual spot-check label, and later
  rejection;
- 15 candidate-summary rows, 100 primary cases, 140 supplemental-v1 cases,
  five PATH-S06 cases, and 29 human-decision rows;
- pagination and candidate, evidence-layer, result, and case-search filters;
- no application page errors or unexpected console errors.

Netlify attempted optional inline hosting-layer injections that the site's
content-security policy blocked. Four corresponding CSP console messages were
classified as expected hosting-layer warnings; the site application remained
functional.

Screenshots:

- `docs/coursework/review-2026-10-22/live-netlify-home.png`
- `docs/coursework/review-2026-10-22/live-netlify-test-evidence.png`

## Interpretation boundary

The live site is a read-only publication of saved evidence. This validation
does not run models, scanners, attacks, or candidate applications and does not
change any study result.
