"""Record Tony Tran's September 22 confirmed supplemental human decisions.

This is intentionally one-shot: record_follow_up refuses to overwrite an
existing result. Primary-v1 reviews, decisions, metrics, and registered test
outcomes are never modified.
"""

from __future__ import annotations

from pathlib import Path

from fixproof.evaluation.supplemental_followup import record_follow_up


ROOT = Path(__file__).resolve().parents[3]
FOLLOW_UP_ROOT = ROOT / "data/supplemental/v1/follow-up-reviews"

SQLI_RATIONALE = """I reviewed the candidate patch, automated primary decision, and all eight supplemental outcomes for this candidate. The patch replaces SQL string concatenation with a parameterized query. The primary target SAST finding resolved, and the candidate passed the original security and functional checks. In the supplement, it passed all three registered SQL-injection security cases, both behavioral-parity cases, and two of three robustness cases. SQL-R01 supplied repeated username parameters and returned HTTP 200 with an empty array instead of the registered HTTP 400 JSON error, so that robustness result remains failed. The response returned no user row and did not broaden the query result. Under my bounded criterion, this client-visible status-code difference is not severe enough to reject the tested SQL-injection repair. I accept the candidate for the bounded benchmark while explicitly retaining the SQL-R01 limitation. This is not full supplemental conformance or production approval, and it does not alter the primary record or metrics."""

PATH_RATIONALES = {
    2: """I reviewed the candidate patch, original acceptance, and all eleven supplemental traversal outcomes. The candidate passed both behavioral-parity cases, all three robustness cases, and all five executable security cases. PATH-S06 remains inconclusive because the Windows environment could not create the required symlink or junction fixture. The patch enforces a lexical resolved-root boundary, but the saved evidence does not establish containment of a filesystem target reached through an in-root link. I therefore request more testing in a symlink-capable environment rather than claiming complete traversal protection. This later conclusion preserves the original bounded acceptance, the inconclusive result, and all primary metrics.""",
    3: """I reviewed the candidate patch, original acceptance, and all eleven supplemental traversal outcomes. The candidate passed both behavioral-parity cases and all five executable security cases. PATH-R01, PATH-R02, and PATH-R03 failed because missing, empty, and repeated filename inputs returned HTTP 404 instead of the registered HTTP 400 response; these are robustness-contract failures, not observed traversal attacks. PATH-S06 remains inconclusive because the Windows environment could not create the required symlink or junction fixture. Because three malformed-input contracts failed and symlink-escape protection remains unverified, I request more testing rather than reaffirming acceptance or claiming complete traversal protection. This later conclusion does not overwrite the original acceptance or primary metrics.""",
    4: """I reviewed the candidate patch, original acceptance, and all eleven supplemental traversal outcomes. The candidate passed both behavioral-parity cases, all three robustness cases, and all five executable security cases. PATH-S06 remains inconclusive because the Windows environment could not create the required symlink or junction fixture. The patch enforces a lexical resolved-root boundary, but the saved evidence does not establish containment of a filesystem target reached through an in-root link. I therefore request more testing in a symlink-capable environment rather than claiming complete traversal protection. This later conclusion preserves the original bounded acceptance, the inconclusive result, and all primary metrics.""",
    5: """I reviewed the candidate patch, original acceptance, and all eleven supplemental traversal outcomes. The candidate passed both behavioral-parity cases, two of three robustness cases, and all five executable security cases. PATH-R03 supplied repeated filenames and returned HTTP 404 with a stable file-not-found response instead of the registered HTTP 400 response. The request exposed no outside content, so I treat this as a robustness-contract limitation rather than an observed traversal attack, and the failed result remains unchanged. PATH-S06 is also inconclusive because the Windows environment could not create the required symlink or junction fixture. I request more testing rather than claiming complete traversal protection. This later conclusion preserves the original acceptance and all primary metrics.""",
}


def record(trial_id: str, verdict: str, rationale: str) -> None:
    directory = FOLLOW_UP_ROOT / trial_id
    result = record_follow_up(
        ROOT,
        directory / "packet.json",
        directory / "result.json",
        "Tony Tran",
        verdict,
        rationale,
        True,
    )
    print(f"{result['trial_id']}: {result['verdict']}")


def main() -> None:
    for attempt in range(1, 6):
        record(
            f"primary-v1-sqli-initial-{attempt:02d}",
            "FOLLOW_UP_ACCEPT_CANDIDATE",
            SQLI_RATIONALE,
        )
    for attempt, rationale in PATH_RATIONALES.items():
        record(
            f"primary-v1-path-traversal-initial-{attempt:02d}",
            "FOLLOW_UP_REQUEST_MORE_TESTING",
            rationale,
        )


if __name__ == "__main__":
    main()
