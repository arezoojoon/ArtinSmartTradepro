"""
Tests for Phase 6 — Eval Harness Runner.
Run: cd backend && python -m pytest tests/test_eval_runner.py -v
"""
import pytest
import subprocess
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).parent.parent


class TestEvalRunner:
    def test_eval_passes_on_valid_fixture(self):
        """The eval runner should return exit code 0 on a passing fixture."""
        # Directly test the run_eval function
        from app.prompt_ops.eval import run_eval
        fixture = {
            "test_name": "Valid output",
            "guardrails": {"no_numeric_without_data": True},
            "input": {"data_used": [{"id": "p1"}]},
            "mock_output": "Based on data, growth is significant.",
            "expected_pass": True,
        }
        result = run_eval(fixture)
        assert result["status"] == "passed"

    def test_eval_fails_on_guardrail_violation(self):
        """The eval runner should detect guardrail failures."""
        from app.prompt_ops.eval import run_eval
        fixture = {
            "test_name": "Hallucination test",
            "guardrails": {"no_numeric_without_data": True},
            "input": {"data_used": []},
            "mock_output": "Growth was 45% and revenue reached $50M.",
            "expected_pass": False,  # We EXPECT this to fail
        }
        result = run_eval(fixture)
        # expected_pass=False means we EXPECT a guardrail failure; matching → PASSED eval
        assert result["status"] == "passed"

    def test_eval_detects_unexpected_pass(self):
        """If output passes when it should fail — the eval is FAILED."""
        from app.prompt_ops.eval import run_eval
        fixture = {
            "test_name": "Should trigger guardrail",
            "guardrails": {"no_numeric_without_data": True},
            "input": {"data_used": []},
            # This output has no numbers — guardrail won't trigger
            "mock_output": "The market shows significant growth potential.",
            "expected_pass": False,  # We expected failure but guardrail didn't trigger
        }
        result = run_eval(fixture)
        # guardrail passes (no numbers), but expected_pass=False → eval FAILS
        assert result["status"] == "failed"

    def test_fixture_loading_for_cultural_strategy(self):
        """Sample fixtures for cultural_strategy should load successfully."""
        from app.prompt_ops.eval import load_fixtures
        fixtures = load_fixtures("cultural_strategy", version=1)
        assert len(fixtures) >= 5, "Expected at least 5 eval fixtures for cultural_strategy"

    def test_all_cultural_strategy_fixtures_run(self):
        """All cultural_strategy/v1 fixtures should be evaluatable."""
        from app.prompt_ops.eval import load_fixtures, run_eval
        fixtures = load_fixtures("cultural_strategy", version=1)
        for f in fixtures:
            result = run_eval(f)
            assert result["status"] in ("passed", "failed"), f"Invalid status for {f.get('test_name')}"

    def test_cli_passes_for_good_fixtures(self):
        """
        CLI should exit 0 when all fixtures pass.
        This is tested by running the cultural_strategy fixtures which are all designed correctly.
        """
        from app.prompt_ops.eval import load_fixtures, run_eval
        fixtures = load_fixtures("cultural_strategy", version=1)
        results = [run_eval(f) for f in fixtures]
        failed = [r for r in results if r["status"] == "failed"]
        # All our sample fixtures are correctly aligned — verify they all pass
        assert len(failed) == 0, f"Some fixtures failed: {failed}"
