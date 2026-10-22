# FixProof Netlify PATH-S06 package validation

Validated October 21, 2026.

## Package

- File: `fixproof-public-netlify-path-s06-2026-10-21-v2.zip`
- SHA-256:
  `F60F2EE42640849C2BD9E89CCE014BD1113B31BF2A4928DD6D47163646B777D0`
- Archive files: 12
- Deployment boundary: `index.html` is at the archive root; the ZIP does not
  contain an extra `fixproof-public/` directory.
- All nested archive entries use forward slashes, including
  `data/public-evidence.json`, `data/student-test-evidence.json`, and
  `assets/fixproof-workflow.png`.

## Correction from version 1

The first October 21 ZIP was produced with Windows `Compress-Archive`. It stored
nested entries with backslashes such as `data\public-evidence.json`. Netlify
could serve the root HTML but returned HTTP 404 when the page requested the
forward-slash JSON path. That package is superseded and must not be deployed.

Version 2 was built with explicit POSIX-style archive entry names. The ZIP was
then extracted to a disposable directory and served from the extracted files.
The browser validator and server log confirmed HTTP 200 for both evidence JSON
requests, the workflow asset, scripts, styles, and both HTML pages.

## Regeneration and validation

The selected public evidence and student report were regenerated from the
current bound repository records before packaging. Local browser validation
then passed for:

- 15 primary candidate rows;
- 15 supplemental candidate rows;
- 10 original human reviews;
- 14 supplemental-v1 human records;
- five PATH-S06 extension candidate records and qualifications;
- 100 primary case rows;
- 140 supplemental-v1 case rows;
- five separate PATH-S06 extension case rows;
- 29 total human-decision rows;
- PATH-S06 candidate details showing HTTP 200, outside-marker disclosure,
  Traversal 02's manual spot-check label, and the later rejection;
- pagination and candidate/layer/result/case-search filters;
- the downloadable seven-sheet workbook; and
- no application page errors or unexpected console errors.

The packaged PATH-S06 summary is zero pass, five fail, and zero inconclusive.
The five original supplemental-v1 PATH-S06 outcomes remain inconclusive and
are not replaced by the extension.

## Privacy checks

The selected JSON exports and archive were checked for local Windows user
paths, WSL user paths, OpenAI response identifiers, and API-key variable names.
No forbidden marker was found. Raw review packets, hashes, credentials, and
local runtime files are not included in the public package.

## Upload procedure

1. Open the existing FixProof site in Netlify.
2. Deploy `fixproof-public-netlify-path-s06-2026-10-21-v2.zip` by drag-and-drop.
3. Wait for Netlify to report that the deployment is published.
4. Open the live site in a private/incognito browser.
5. Confirm the home-page metrics include `5/5 PATH-S06 extension failures`.
6. Open `test-evidence.html`, search for `PATH-S06`, and confirm ten matching
   rows: five frozen supplemental-v1 inconclusive rows and five extension
   failure rows.
7. Open Traversal 02 and confirm its extension evidence shows HTTP 200,
   outside-marker disclosure, the manual spot-check label, and rejection.
8. Download the workbook and open the PATH-S06 Extension worksheet.
9. Confirm the PDF appendix and workflow image load and browser developer tools
   show no failed site requests.

The live deployment is not claimed as updated by this local validation record.
Record the live check separately after upload.
