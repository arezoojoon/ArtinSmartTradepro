"""
Tests for Phase 6 — Prompt Ops Guardrails & Runtime Service.
Run: cd backend && python -m pytest tests/test_prompt_ops.py -v
"""
import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from fastapi import HTTPException


class TestGuardrailChecker:
    """Tests for check_guardrails — the core LLM output validator."""

    def test_empty_output_fails(self):
        from app.services.prompt_ops import check_guardrails
        result = check_guardrails("", {}, {})
        assert result["pass"] is False
        assert any("empty" in r.lower() for r in result["reasons"])

    def test_numeric_output_without_data_fails(self):
        from app.services.prompt_ops import check_guardrails
        result = check_guardrails(
            output="The market grew by 45% and sales reached 50,000 tons.",
            guardrail_config={"no_numeric_without_data": True},
            input_data={"data_used": []},
        )
        assert result["pass"] is False
        assert any("numeric" in r.lower() or "GUARDRAIL" in r for r in result["reasons"])

    def test_numeric_output_with_data_passes(self):
        from app.services.prompt_ops import check_guardrails
        result = check_guardrails(
            output="Based on provided data, 45% growth observed.",
            guardrail_config={"no_numeric_without_data": True},
            input_data={"data_used": [{"profile_id": "p1"}]},
        )
        assert result["pass"] is True

    def test_missing_profile_citation_fails(self):
        from app.services.prompt_ops import check_guardrails
        result = check_guardrails(
            output="This buyer prefers relationship-based negotiations.",
            guardrail_config={"must_cite_profiles": True},
            input_data={"profile_ids": ["prof-001"]},
        )
        assert result["pass"] is False

    def test_profile_citation_present_passes(self):
        from app.services.prompt_ops import check_guardrails
        result = check_guardrails(
            output="Based on referenced_profile_ids: [prof-001], trust-based approach is advised.",
            guardrail_config={"must_cite_profiles": True},
            input_data={"profile_ids": ["prof-001"]},
        )
        assert result["pass"] is True

    def test_missing_insufficient_data_notice_fails(self):
        from app.services.prompt_ops import check_guardrails
        result = check_guardrails(
            output="The strategy for this buyer is to be very friendly.",
            guardrail_config={"require_insufficient_data_notice": True},
            input_data={"profile_missing": True},
        )
        assert result["pass"] is False

    def test_insufficient_data_notice_present_passes(self):
        from app.services.prompt_ops import check_guardrails
        result = check_guardrails(
            output="INSUFFICIENT DATA: No buyer profile found. Please collect data first.",
            guardrail_config={"require_insufficient_data_notice": True},
            input_data={"profile_missing": True},
        )
        assert result["pass"] is True

    def test_no_guardrails_configured_passes(self):
        from app.services.prompt_ops import check_guardrails
        result = check_guardrails(
            output="Some output text without any restrictions.",
            guardrail_config={},
            input_data={},
        )
        assert result["pass"] is True


class TestGetActiveVersion:
    def test_no_approved_version_raises_503(self):
        from app.services.prompt_ops import get_active_version

        mock_db = MagicMock()
        mock_family = MagicMock()
        mock_family.id = uuid4()
        mock_family.name = "test_family"

        # Simulate: family exists but no approved version
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_family,  # family query
            None,         # version query (no approved)
        ]

        with pytest.raises(HTTPException) as exc_info:
            get_active_version(mock_db, "test_family")
        assert exc_info.value.status_code == 503
        assert "approved" in exc_info.value.detail.lower()

    def test_unknown_family_raises_503(self):
        from app.services.prompt_ops import get_active_version

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_active_version(mock_db, "nonexistent_family")
        assert exc_info.value.status_code == 503


class TestPromptRendering:
    def test_render_replaces_variables(self):
        from app.services.prompt_ops import render_prompt
        from app.models.phase6 import PromptVersion

        version = MagicMock(spec=PromptVersion)
        version.system_prompt = "You are a {{persona}} assistant."
        version.user_prompt_template = "Analyze {{product}} for {{country}}."

        system, user = render_prompt(version, {"persona": "trade", "product": "dates", "country": "UAE"})
        assert system == "You are a trade assistant."
        assert user == "Analyze dates for UAE."

    def test_render_leaves_unused_placeholders(self):
        from app.services.prompt_ops import render_prompt
        from app.models.phase6 import PromptVersion

        version = MagicMock(spec=PromptVersion)
        version.system_prompt = "Hello {{name}}."
        version.user_prompt_template = "Analyze {{product}}."

        system, user = render_prompt(version, {"product": "rice"})
        assert "{{name}}" in system   # Unused placeholder stays
        assert "rice" in user
