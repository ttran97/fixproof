# Progress Report 3 writing starter

Prepared from evidence reviewed September 21, 2026. Transfer into the actual course template and retain every required component. This is a writing aid, not a completed submission. Supply your actual reporting period, hours, name/course fields, and verified AI-use disclosure. Do not double-count work already reported in Report 2.

## Updated problem and approach

FixProof investigates how separately recorded static, runtime-security, and functional evidence can support review of AI-generated vulnerability repairs. The current scope is three purpose-built JavaScript/Express applications with XSS, SQL injection, and path-traversal vulnerabilities. Python coordinates scanning, candidate generation, validation, evidence reporting, and review. The repair model proposes changes; predefined tests and deterministic policy evaluate them before human review. This controlled study evaluates AI-generated repairs, rather than a representative population of AI-generated applications.

## Work completed and contribution

Since the checkpoint used in Report 2, the ten primary conflict reviews have been completed. Seven accepted the candidate under the original evidence and three requested additional testing. These original reviews were already described in Video II. The main subsequent contribution is a predefined supplemental evaluation of the three frozen baselines and all fifteen saved candidates, using the same registered cases for each comparable candidate without new model calls or SAST rescanning.

The supplement separates security, behavioral parity, and newly defined robustness requirements. Its 140 candidate-case observations comprise 55 security passes and five inconclusive security cases; 40 parity passes and five failures; and 25 robustness passes and ten failures. Four XSS candidates changed missing-input output, and one traversal candidate rejected a legitimate in-root filename. All five SQLi candidates missed a newly defined repeated-parameter rejection rule; this is a supplemental robustness limitation, not a retroactive primary security failure. The traversal symlink case could not execute because Windows denied fixture creation, so it remains inconclusive.

Separate September 15 follow-up reviews rejected XSS candidates 04 and 05 and traversal candidate 01, preserving the original review records. On September 21, Tony applied the same frozen parity criterion to XSS 01 and 02 and recorded separate rejection qualifications; their original primary acceptances remain unchanged. On September 22, Tony recorded bounded acceptances for SQLi 01–05 while retaining each `SQL-R01` robustness failure, and requests for more testing for traversal 02–05 while retaining the inconclusive symlink results and robustness limitations. These findings demonstrate that passing the original fixed tests did not exhaust relevant application behavior. The current repository passes 119 automated tests, both primary and supplemental evidence checks pass, and all 14 supplemental human packet/result bindings verify. These software checks are distinct from new application experiments.

## Interpretation, limitations, and feedback response

The primary experiment remains fifteen initial repair attempts, five candidates ready for human review, ten SAST/runtime disagreements, and zero observed primary false successes. These outcomes describe this small controlled study and do not establish general security or production readiness. Supplemental results must remain separate from primary metrics. Repeated repairs of three fixtures also provide limited application diversity.

The supplemental behavior findings directly address feedback about functional test sufficiency and unexpected changes introduced by fixes. The frozen inputs, explicit oracles, retained evidence, and separate follow-up decisions make the evaluation more systematic. Further justification of design alternatives and comparison with prior repair research are still needed to fully address the professor's feedback.

## Next reporting period

- Disclose the completed XSS 01–02 qualifications and the traversal and SQLi robustness limitations without rewriting primary metrics.
- Decide whether to retain the symlink limitation or collect a separately documented environment-capable follow-up.
- Expand the related-work comparison and draft the final methods/results sections with explicit success criteria and denominators.
- Rehearse Video III using a saved candidate, its validation evidence, and the supplemental follow-up decision; prepare a clean submission verification checklist.

## Personal fields to complete

- Reporting period: [actual start and end dates].
- Hours this period and cumulative hours: [your contemporaneous records or clearly labeled honest estimate; do not infer from commit count].
- AI assistance: [actual tools/models and uses; retain/cite actual prompts as required by the syllabus, and personally verify this text].
- References: [checked research papers and specific technical references used for these methods; use consistent bibliographic labels].
- Any template-specific schedule, obstacles, or draft-paper fields: [complete rather than omit].
