from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fixproof.primary_trials import (
    DEFAULT_OUTPUT_ROOT,
    PrimaryTrialError,
    audit_prompt_withholding,
    build_collection_state,
    build_dry_run,
    build_schedule,
    collection_implementation_bindings,
    prepare_case,
    run_one_attempt,
    select_scheduled_attempts,
    validate_frozen_inputs,
)


class PrimaryTrialRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.project_root = Path(__file__).resolve().parents[1]

    def _output_snapshot(self) -> dict[str, bytes]:
        output_root = self.project_root / DEFAULT_OUTPUT_ROOT
        if not output_root.exists():
            return {}
        return {
            path.relative_to(output_root).as_posix(): path.read_bytes()
            for path in output_root.rglob("*")
            if path.is_file()
        }

    def test_dry_run_schedules_fifteen_without_repository_writes(self) -> None:
        before = self._output_snapshot()
        result = build_dry_run(self.project_root)
        after = self._output_snapshot()

        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["model_calls_performed"], 0)
        self.assertFalse(result["writes_performed"])
        self.assertEqual(before, after)
        self.assertEqual(len(result["schedule"]), 15)
        self.assertEqual(len(result["preparations"]), 3)
        self.assertTrue(
            all(
                item["prompt_withholding_audit"] == "pass"
                for item in result["preparations"]
            )
        )

    def test_schedule_is_five_initial_attempts_per_case(self) -> None:
        frozen = validate_frozen_inputs(self.project_root)
        schedule = build_schedule(frozen)

        for case_id in ("xss", "sqli", "path-traversal"):
            case_attempts = [
                item for item in schedule if item["case_id"] == case_id
            ]
            self.assertEqual(
                [item["attempt"] for item in case_attempts],
                [1, 2, 3, 4, 5],
            )
            self.assertTrue(
                all(item["condition"] == "initial" for item in case_attempts)
            )
            self.assertTrue(
                all(item["metric_scope"] == "primary" for item in case_attempts)
            )

    def test_collection_implementation_is_hash_bound(self) -> None:
        bindings = collection_implementation_bindings(self.project_root)

        self.assertIn("src/fixproof/primary_trials.py", bindings)
        self.assertIn(
            "src/fixproof/validation/decision_engine.py",
            bindings,
        )
        self.assertTrue(
            all(len(digest) == 64 for digest in bindings.values())
        )

    def test_changed_frozen_input_is_rejected(self) -> None:
        plan_path = self.project_root / "data/evaluation/trial-plan.json"
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        changed = copy.deepcopy(plan)
        changed["freeze_evidence"]["initial_prompt_template"]["sha256"] = (
            "0" * 64
        )

        with self.assertRaisesRegex(PrimaryTrialError, "Frozen input changed"):
            validate_frozen_inputs(self.project_root, plan=changed)

    def test_prompt_withholding_rejects_hidden_payload(self) -> None:
        frozen = validate_frozen_inputs(self.project_root)
        case = frozen["manifest"]["cases"][0]
        leaked = {
            "prompts": [
                {"user_prompt": "Try <script>alert(1)</script> as the test."}
            ]
        }

        with self.assertRaisesRegex(PrimaryTrialError, "leaked"):
            audit_prompt_withholding(case, leaked)

    def test_attempt_selector_is_bounded(self) -> None:
        frozen = validate_frozen_inputs(self.project_root)
        schedule = build_schedule(frozen)

        selected = select_scheduled_attempts(schedule, "sqli", 3)
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]["trial_id"], "primary-v1-sqli-initial-03")
        with self.assertRaisesRegex(PrimaryTrialError, "requires --case"):
            select_scheduled_attempts(schedule, None, 1)

    def test_uncertain_api_state_never_calls_model_again(self) -> None:
        scheduled = {
            "trial_id": "primary-v1-xss-initial-01",
            "case_id": "xss",
            "application": "primary-xss-v1",
            "cwe": "CWE-79",
            "attempt": 1,
            "condition": "initial",
            "metric_scope": "primary",
            "status": "planned",
        }

        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory)
            attempt_directory = output_root / "cases/xss/attempt-01"
            attempt_directory.mkdir(parents=True)
            state = {
                "trial_id": scheduled["trial_id"],
                "status": "api_request_started",
            }
            (attempt_directory / "attempt.json").write_text(
                json.dumps(state),
                encoding="utf-8",
            )

            def forbidden_model_call(**_: object) -> dict:
                self.fail("An uncertain attempt must not call the model again.")

            result = run_one_attempt(
                self.project_root,
                {},
                {"case_id": "xss"},
                scheduled,
                {},
                output_root,
                remediation_runner=forbidden_model_call,
            )

        self.assertEqual(result["status"], "api_request_started")

    def test_collection_metrics_use_only_the_fifteen_slot_schedule(self) -> None:
        frozen = validate_frozen_inputs(self.project_root)
        schedule = build_schedule(frozen)

        with tempfile.TemporaryDirectory() as directory:
            output_root = Path(directory)
            first = schedule[0]
            attempt_directory = output_root / "cases/xss/attempt-01"
            attempt_directory.mkdir(parents=True)
            record = {
                **first,
                "status": "completed",
                "disposition": "REJECT",
                "classification": "sast_false_success",
                "sast_only_interpretation": "APPARENT_SUCCESS",
                "evidence": {
                    "target_sast": "resolved",
                    "new_sast_findings": 0,
                    "security_validation": "pass",
                    "functional_validation": "fail",
                },
                "evaluation_labels": {"false_success": True},
            }
            (attempt_directory / "attempt.json").write_text(
                json.dumps(record),
                encoding="utf-8",
            )

            state = build_collection_state(output_root, schedule)

        self.assertEqual(state["scheduled"], 15)
        self.assertEqual(state["terminal"], 1)
        self.assertTrue(state["primary_metrics"]["provisional"])
        self.assertEqual(
            state["primary_metrics"]["sast_false_success"],
            {"count": 1, "denominator": 15, "rate": 1 / 15},
        )

    def test_completed_attempt_is_resumable_without_second_model_call(self) -> None:
        frozen = validate_frozen_inputs(self.project_root)
        case = frozen["manifest"]["cases"][0]
        scheduled = build_schedule(frozen)[0]
        calls = 0

        def write(path: Path, payload: dict) -> dict:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload), encoding="utf-8")
            return payload

        def fake_remediation(**kwargs: object) -> dict:
            nonlocal calls
            calls += 1
            output = kwargs["output_file"]
            assert isinstance(output, Path)
            payload = {
                "remediation": {
                    "canonical_id": kwargs["canonical_id"],
                    "model": kwargs["model"],
                    "response_id": "response-test",
                    "patched_code": (
                        'app.get("/hello", (req, res) => {\n'
                        "    const name = req.query.name;\n"
                        '    res.send("<h1>Hello " + name + "</h1>");\n'
                        "});"
                    ),
                    "needs_additional_context": False,
                }
            }
            return write(output, payload)

        def fake_preliminary(**kwargs: object) -> dict:
            output = kwargs["output_file"]
            assert isinstance(output, Path)
            payload = {
                "validation": {
                    "canonical_id": kwargs["canonical_id"],
                    "syntax": {"status": "pass"},
                }
            }
            return write(output, payload)

        def fake_security(**kwargs: object) -> dict:
            output = kwargs["output_file"]
            assert isinstance(output, Path)
            payload = {
                "security_validation": {
                    "canonical_id": kwargs["canonical_id"],
                    "status": "pass",
                }
            }
            return write(output, payload)

        def fake_functional(**kwargs: object) -> dict:
            output = kwargs["output_file"]
            assert isinstance(output, Path)
            payload = {
                "functional_validation": {
                    "canonical_id": kwargs["canonical_id"],
                    "status": "pass",
                }
            }
            return write(output, payload)

        def fake_decision(**kwargs: object) -> dict:
            output = kwargs["output_file"]
            assert isinstance(output, Path)
            payload = {
                "decision": {
                    "classification": "validated_candidate",
                    "disposition": "READY_FOR_HUMAN_REVIEW",
                    "evidence": {
                        "target_sast": "resolved",
                        "new_sast_findings": 0,
                        "security_validation": "pass",
                        "functional_validation": "pass",
                    },
                    "evaluation_labels": {"false_success": False},
                }
            }
            return write(output, payload)

        with tempfile.TemporaryDirectory(
            prefix="primary-runner-test-",
            dir=self.project_root,
        ) as directory:
            output_root = Path(directory)
            preparation = prepare_case(
                self.project_root,
                frozen,
                case,
                output_root / "preparation/xss",
            )
            with (
                mock.patch(
                    "fixproof.primary_trials.run_validation",
                    side_effect=fake_preliminary,
                ),
                mock.patch(
                    "fixproof.primary_trials.run_security_validation",
                    side_effect=fake_security,
                ),
                mock.patch(
                    "fixproof.primary_trials.run_functional_validation",
                    side_effect=fake_functional,
                ),
                mock.patch(
                    "fixproof.primary_trials.run_decision_engine",
                    side_effect=fake_decision,
                ),
            ):
                first = run_one_attempt(
                    self.project_root,
                    frozen,
                    case,
                    scheduled,
                    preparation,
                    output_root,
                    remediation_runner=fake_remediation,
                )
                second = run_one_attempt(
                    self.project_root,
                    frozen,
                    case,
                    scheduled,
                    preparation,
                    output_root,
                    remediation_runner=fake_remediation,
                )

        self.assertEqual(first["status"], "completed")
        self.assertEqual(second["status"], "completed")
        self.assertEqual(calls, 1)


if __name__ == "__main__":
    unittest.main()
