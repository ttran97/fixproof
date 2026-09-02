# FixProof Progress Report I Submission Checklist

Use this checklist before renaming the draft and uploading it to Canvas.

## Required personal confirmations

- Confirm that **CS** is the correct section designation.
- Confirm that **Tony Tran** is the name exactly as it should appear.
- Replace the suggested completed-task hour allocations with your actual time
  log. The syllabus expects approximately **30 hours over two weeks**; do not
  claim hours you did not work.
- Confirm the reporting period and every week/date against Canvas. The draft
  derives weekly ranges from the template's W1 date and does not replace the
  official Canvas calendar.
- Add any proposal/instructor feedback you received and state specifically how
  the problem, scope, or deliverables changed because of it. The syllabus says
  Progress Report I should refine and better scope the proposal based on
  feedback.

## Academic integrity and AI disclosure

- Keep the generative-AI disclosure in the appendix and edit it so it precisely
  identifies every tool/model you actually used.
- Retain or attach a sanitized prompt/output log as instructed by the course.
  Do **not** include API keys, `.env`, credentials, or unredacted secrets.
- Verify every factual claim and reference. The student is responsible for the
  submitted work even when AI tools were used.
- Review the Turnitin/similarity result, add quotation marks or citations where
  needed, and revise prose into your own verified voice before the deadline.

## CS6727 alignment check

- The report defines a real technical cybersecurity problem and cites external
  evidence.
- The solution has a concrete implemented prototype and bounded deliverables.
- The methodology systematically separates ground truth, SAST, runtime
  security, functionality, deterministic policy, and human review.
- The evaluation identifies measurable outcomes, current pilot results, a
  SAST-only comparison, repetition plans, and limitations.
- The timeline covers the full semester with actionable project tasks and one
  task per row; it excludes peer feedback and progress-report administration.
- Scope remains a controlled JavaScript/Express research prototype—not a
  production SAST replacement, autonomous patch deployer, or universal code
  repair system.
- The report explicitly addresses efficacy, limitations, privacy, deployment
  feasibility, and reproducibility, matching the final-course objectives.

## Final file checks

- Open the DOCX in Microsoft Word and check page breaks, table wrapping,
  headings, bullets, and reference formatting.
- Accept or remove any accidental tracked changes/comments.
- Remove `DRAFT` from the filename only after all confirmations are complete.
- Run `python -m fixproof.reproduce --verify` with the project virtual
  environment and ensure the reported metrics still match the document.
- Upload before the Canvas deadline in the required format and verify the
  uploaded file opens correctly.
