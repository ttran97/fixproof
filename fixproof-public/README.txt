FIXPROOF PUBLIC REFERENCE - NETLIFY UPLOAD

This is a static, read-only coursework reference. It contains a selected public
evidence export, not the raw FixProof repository.

Upload options:

1. Drag this entire folder to https://app.netlify.com/drop
2. Or upload the companion versioned Netlify ZIP package supplied with this
   export.

The deployed root must contain index.html. No build command, database, server,
environment variables, API key, or Netlify Function is required.

After deployment, verify:

- The workflow image loads.
- The Primary and Supplemental tables each show 15 candidates.
- The snapshot shows 140 supplemental-v1 observations and 5/5 PATH-S06
  extension failures as separate metrics.
- Candidate details show the appropriate original, supplemental-v1, and
  PATH-S06 extension rationales.
- The Test cases page opens and shows 15 candidate rows, 245 case-evidence
  rows, the count reconciliation table, and 29 human-decision records.
- The Excel workbook downloads and contains seven worksheets.
- The evidence appendix opens.
- Browser developer tools show no failed requests.

Do not replace data/public-evidence.json or
data/student-test-evidence.json with raw repository JSON files. The public
exports intentionally omit local-user paths, OpenAI response identifiers,
hashes, and review packets.
