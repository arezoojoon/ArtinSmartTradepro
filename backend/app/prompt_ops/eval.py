"""
Phase 6 — Prompt Eval Harness CLI
Run: python -m app.prompt_ops.eval --family cultural_strategy --version 1

Exit code 0 = all tests pass
Exit code 1 = one or more tests failed (CI gate)
"""
import argparse
import sys
import json
import os
import yaml
from pathlib import Path
from typing import Optional

# Allow running as __main__
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from app.services.prompt_ops import check_guardrails


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixtures(family_name: str, version: Optional[int]) -> list[dict]:
    """Load eval fixtures from YAML files."""
    fixtures = []

    # Try family-specific file first
    fam_file = FIXTURES_DIR / f"{family_name}_evals.yaml"
    if fam_file.exists():
        with open(fam_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            for item in data.get("evals", []):
                if version is None or item.get("version") == version:
                    fixtures.append(item)
    else:
        print(f"[WARN] No fixture file found: {fam_file}", file=sys.stderr)

    return fixtures


def run_eval(fixture: dict) -> dict:
    """
    Run a single eval case.
    Returns: {"test_name": str, "status": "passed"|"failed", "reasons": []}
    """
    test_name = fixture.get("test_name", "unnamed")
    input_data = fixture.get("input", {})
    mock_output = fixture.get("mock_output", "")
    guardrail_config = fixture.get("guardrails", {})
    expected_pass = fixture.get("expected_pass", True)

    result = check_guardrails(mock_output, guardrail_config, input_data)
    actual_pass = result["pass"]

    if actual_pass == expected_pass:
        return {"test_name": test_name, "status": "passed", "reasons": result["reasons"]}
    else:
        return {
            "test_name": test_name,
            "status": "failed",
            "reasons": result["reasons"],
            "expected_pass": expected_pass,
            "actual_pass": actual_pass,
            "mock_output_preview": mock_output[:200],
        }


def print_result(r: dict):
    icon = "✅" if r["status"] == "passed" else "❌"
    print(f"  {icon} [{r['status'].upper()}] {r['test_name']}")
    if r["status"] == "failed":
        for reason in r.get("reasons", []):
            print(f"      ↳ {reason}")
        if "expected_pass" in r:
            print(f"      ↳ Expected pass={r['expected_pass']}, got pass={r['actual_pass']}")


def main():
    parser = argparse.ArgumentParser(description="Artin Prompt Ops Eval Runner")
    parser.add_argument("--family", required=True, help="Prompt family name (e.g. cultural_strategy)")
    parser.add_argument("--version", type=int, default=None, help="Version number (omit = all)")
    parser.add_argument("--json", dest="json_output", action="store_true", help="Output JSON results")
    args = parser.parse_args()

    print(f"\n🔬 Artin Prompt Eval Runner")
    print(f"   Family:  {args.family}")
    print(f"   Version: {args.version or 'all'}")
    print(f"   Fixtures: {FIXTURES_DIR}\n")

    fixtures = load_fixtures(args.family, args.version)
    if not fixtures:
        print(f"[ERROR] No eval fixtures found for family='{args.family}' version={args.version}")
        sys.exit(1)

    results = []
    for fixture in fixtures:
        r = run_eval(fixture)
        results.append(r)
        if not args.json_output:
            print_result(r)

    passed = sum(1 for r in results if r["status"] == "passed")
    failed = sum(1 for r in results if r["status"] == "failed")

    if args.json_output:
        print(json.dumps({"passed": passed, "failed": failed, "results": results}, indent=2))
    else:
        print(f"\n{'─' * 50}")
        print(f"  Results: {passed} passed, {failed} failed out of {len(results)} tests")
        if failed > 0:
            print(f"  ❌ EVAL FAILED — blocking deployment")
        else:
            print(f"  ✅ ALL EVALS PASSED")
        print()

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
