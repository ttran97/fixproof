# FixProof Related-Work Positioning

## Purpose

This working document positions FixProof without claiming that it invented
LLM vulnerability repair, patch validation, or validation-guided retry. The
project contribution is a controlled, auditable combination of those ideas for
three JavaScript/Express security benchmarks.

## Initial comparison

| Work | What it establishes | Relationship to FixProof |
|---|---|---|
| Pearce et al. (2022), *Asleep at the Keyboard?* | AI-generated code can contain security weaknesses across controlled CWE scenarios. | Motivates treating model output as untrusted and requiring independent evidence. |
| Pearce et al. (2023), *Examining Zero-Shot Vulnerability Repair with Large Language Models* | LLMs can be evaluated as candidate vulnerability-repair generators rather than trusted fix authorities. | FixProof narrows the setting to an auditable pipeline that retains the candidate and each validation stage. |
| Kulsum et al. (2024), *A Case Study of LLM for Automated Vulnerability Repair* | Patch-validation feedback can be used as part of an LLM vulnerability-repair workflow. | FixProof preserves retry lineage and measures improvement while keeping the model outside the final decision. |

## Proposed contribution statement

FixProof is not proposed as a new general-purpose repair algorithm. It is a
validation-oriented AppSec prototype that demonstrates how an AI-generated
candidate can be handled as untrusted input and evaluated through separately
recorded SAST, targeted runtime-security, functional-regression, deterministic
policy, and human-review channels. Its empirical contribution is the evidence
from a small controlled benchmark, including a caught functional regression,
SAST/runtime disagreements, a validation-guided retry, and a separated non-AI
false-success control.

## Questions to resolve before the next report

- Which prior systems retain immutable, stage-level evidence rather than only
  reporting a final patch-success label?
- Which studies compare SAST-only interpretation with runtime and functional
  evidence for the same candidate?
- How do prior studies define a successful repair and detect behavior change?
- Which validation-feedback systems allow retries, and how do they prevent the
  generator from approving its own output?
- Is FixProof's strongest distinction its evidence model, deterministic
  disposition policy, human-adjudication boundary, or their integration?

## Starter references

1. Pearce, H., Ahmad, B., Tan, B., Dolan-Gavitt, B., and Karri, R. (2022).
   *Asleep at the Keyboard? Assessing the Security of GitHub Copilot's Code
   Contributions.* IEEE Symposium on Security and Privacy.
   <https://doi.org/10.1109/SP46214.2022.9833571>
2. Pearce, H., Tan, B., Ahmad, B., Karri, R., and Dolan-Gavitt, B. (2023).
   *Examining Zero-Shot Vulnerability Repair with Large Language Models.* IEEE
   Symposium on Security and Privacy. <https://ieeexplore.ieee.org/document/10179324>
3. Kulsum, U., Zhu, H., Xu, B., and d'Amorim, M. (2024). *A Case Study of LLM
   for Automated Vulnerability Repair: Assessing Impact of Reasoning and Patch
   Validation Feedback.* AIware '24. <https://doi.org/10.1145/3664646.3664770>

All claims and bibliographic fields should be checked against the papers before
this draft is incorporated into a graded report.

