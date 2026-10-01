# FixProof Progress Report 4 next steps

Updated October 1, 2026 after the student case-evidence report was validated.

## Immediate next action

Upload `fixproof-public-netlify-test-evidence-2026-10-01.zip` when Tony is
ready to replace the current public reference, then verify the live dashboard,
test-evidence page, filters, workbook download, and appendix. After publishing,
focus on Video III peer feedback, actual hours, and the broader clean-package
audit.

## Chronological plan

1. **September 30: preserve the completed extension checkpoint.** The frozen
   `path-s06-extension-v1` run is complete and verified at zero candidate pass,
   five fail, and zero inconclusive. Primary-v1 and supplemental-v1 remained
   unchanged.
2. **September 30: complete the extension human review.** Tony reviewed the
   summary, candidate records, and saved patches and manually reproduced
   Traversal 02. Five separate rejection qualifications are recorded and
   verified; all prior records remain preserved.
3. **September 30-October 6: preserve the posted-video checkpoint.** Save the
   submission receipt or screenshot and keep the final deck, script, dashboard
   URL, and recording date together. Do not treat posting the video as a new
   experiment.
4. **October 1: preserve the student evidence checkpoint.** The workbook,
   CSV tables, count reconciliation, and public test-evidence page are complete
   and locally validated. They expose 100 primary, 140 supplemental-v1, and
   five extension rows without changing frozen evidence.
5. **October 1-11: deploy and live-validate the public package.** Upload the
   October 1 ZIP. Confirm the test-evidence page loads 15 candidate rows, the
   filters reach all 245 case rows, the workbook downloads, and no private
   paths or failed requests appear.
6. **October 1-11: complete and summarize peer feedback.** Finish Peer Feedback
   Report III by October 11. Summarize themes rather than copying comments into
   the report without analysis.
7. **October 8-15: perform the reproducibility and report audit.** Recheck
   primary evidence, supplemental evidence, human-record bindings, controls,
   extension bindings, failure handling, public export, references, actual
   hours, and limitations. Update the working draft only with completed
   evidence.
8. **October 15-17: regenerate the report and public reference.** Keep the
   supplemental-v1 140-observation totals unchanged and show PATH-S06 as a
   separate five-candidate extension. The public source and evidence appendix
   are complete; inspect the final Word/PDF rendering after adding feedback and
   actual hours.
9. **October 18: inspect and submit.** Confirm live Canvas instructions, inspect
   the final DOCX/PDF for page breaks and stale placeholders, submit by the
   listed 11:59 p.m. deadline, and retain the receipt.

## PATH-S06 decision rule

- Fixture: an in-root link named `link` points to a disposable directory
  outside the allowed root.
- Request: `link/outside-secret.txt`.
- Baseline expectation: the vulnerable baseline returns the outside marker. If
  the expected baseline behavior is wrong, stop before candidate execution and
  revise the plan as a new version.
- Candidate pass: the outside marker is absent and the response is HTTP 400,
  403, or 404.
- Candidate fail: outside content is disclosed.
- Inconclusive: the environment cannot create the link or cannot execute the
  case reliably.

The completed result qualifies the existing evidence. It does not overwrite the
five original supplemental-v1 inconclusive observations.

## Environment and run completed September 30

- WSL2 Ubuntu provided Linux kernel 6.6.87.2, Python 3.12.3, and native Linux
  Node.js 24.19.0/npm 11.17.0.
- The Node.js archive checksum matched Node.js's official manifest.
- Dependencies were restored from the committed lockfile. Candidate workspaces
  and link fixtures were created under Linux-native disposable temporary
  directories; only the evidence outputs were written to the project tree.
- Six focused oracle tests passed before execution on Windows Python 3.11.9 and
  WSL2 Python 3.12.3. A seventh post-run test verifies the frozen protocol and
  all bound input hashes.
- Run ID: `20260930T180925912688Z-path-s06-v1`.
- Baseline gate: pass. Candidate counts: zero pass, five fail, zero
  inconclusive. All five failures disclosed the controlled marker over HTTP
  200.
- No second candidate run is planned under the frozen stopping rule.

## Information Tony must still supply

- Actual work dates and personal hours after the September 28 Report 3
  submission.
- Video III submission receipt/date if a formal receipt is available.
- Peer feedback and Tony's disposition for each substantive comment.
- Confirmation that the October 1 Netlify package is live and its
  test-evidence page and workbook were checked.
- Confirmation of the live October 18 Canvas deadline before submission.
