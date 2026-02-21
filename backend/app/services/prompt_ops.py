"""
Phase 6 — Prompt Ops Runtime Service
Handles prompt selection, guardrail enforcement, and run logging.
LLM is NEVER allowed to bypass guardrails.
"""
from datetime import datetime
from typing import Optional, Any
from uuid import UUID, uuid4
import re

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.phase6 import PromptFamily, PromptVersion, PromptRun


# ─── Guardrail checker ────────────────────────────────────────────────────────

def check_guardrails(
    output: str | dict,
    guardrail_config: dict,
    input_data: dict,
) -> dict:
    """
    Checks model output against guardrail rules.
    Returns: {"pass": bool, "reasons": [str]}

    Non-negotiable rules (always applied regardless of config):
      - Output must be a non-empty string
    Config-driven rules:
      - no_numeric_without_data: reject if output contains numbers but data_used is empty
      - must_cite_profiles: reject if output lacks referenced_profile_ids
      - require_insufficient_data_notice: reject if profile_missing=True but output lacks "INSUFFICIENT DATA"
    """
    reasons = []

    # Normalise output to string
    if isinstance(output, dict):
        output_text = output.get("text", "") or str(output)
    else:
        output_text = str(output) if output else ""

    if not output_text.strip():
        return {"pass": False, "reasons": ["Output is empty"]}

    # Rule: no_numeric_without_data
    if guardrail_config.get("no_numeric_without_data", False):
        data_used = input_data.get("data_used", input_data.get("profiles", []))
        has_numbers = bool(re.search(r"\d+(?:\.\d+)?%?", output_text))
        if has_numbers and not data_used:
            reasons.append(
                "GUARDRAIL: output contains numeric claims but input data_used is empty. "
                "Model must not invent statistics."
            )

    # Rule: must_cite_profiles
    if guardrail_config.get("must_cite_profiles", False):
        cited = re.findall(r"referenced_profile_ids?[:\s]+\[?([^\]\n]+)\]?", output_text, re.IGNORECASE)
        profile_ids_in_input = input_data.get("profile_ids", input_data.get("profiles", []))
        if profile_ids_in_input and not cited:
            reasons.append(
                "GUARDRAIL: output must include referenced_profile_ids when profiles are provided."
            )

    # Rule: require_insufficient_data_notice
    if guardrail_config.get("require_insufficient_data_notice", False):
        profile_missing = input_data.get("profile_missing", False)
        if profile_missing and "INSUFFICIENT DATA" not in output_text.upper():
            reasons.append(
                "GUARDRAIL: profile_missing=True but output does not contain required "
                "'INSUFFICIENT DATA' notice."
            )

    return {"pass": len(reasons) == 0, "reasons": reasons}


# ─── Prompt selection ─────────────────────────────────────────────────────────

def get_active_version(db: Session, family_name: str) -> PromptVersion:
    """
    Returns the latest approved PromptVersion for the given family.
    Raises HTTP 503 if no approved version exists.
    """
    family = db.query(PromptFamily).filter(
        PromptFamily.name == family_name,
        PromptFamily.is_active == True,
    ).first()

    if not family:
        raise HTTPException(
            status_code=503,
            detail=f"Prompt family '{family_name}' not found or inactive. [NOT IMPLEMENTED]",
        )

    version = (
        db.query(PromptVersion)
        .filter(
            PromptVersion.family_id == family.id,
            PromptVersion.status == "approved",
        )
        .order_by(PromptVersion.version.desc())
        .first()
    )

    if not version:
        raise HTTPException(
            status_code=503,
            detail=(
                f"No approved prompt version for family '{family_name}'. "
                "Draft versions must be approved by a sys admin before use."
            ),
        )

    return version


def render_prompt(version: PromptVersion, variables: dict) -> tuple[str, str]:
    """
    Renders system_prompt and user_prompt_template with provided variables.
    Returns (system_prompt, user_prompt).
    """
    system = version.system_prompt
    user = version.user_prompt_template
    for key, value in variables.items():
        placeholder = "{{" + key + "}}"
        system = system.replace(placeholder, str(value))
        user = user.replace(placeholder, str(value))
    return system, user


# ─── Runtime pipeline ─────────────────────────────────────────────────────────

def run_prompt(
    db: Session,
    *,
    tenant_id: UUID,
    family_name: str,
    input_data: dict,
    variables: dict,
    engine_run_id: Optional[UUID] = None,
    llm_caller,   # callable(system_prompt, user_prompt) -> {"text": str, "token_usage": dict}
) -> dict:
    """
    Full Prompt Ops pipeline:
      1. Select active approved version
      2. Render prompts
      3. Call LLM via llm_caller
      4. Run guardrail checker on output
      5. Store PromptRun record
      6. Return result or raise if guardrail fails

    llm_caller signature: (system_prompt: str, user_prompt: str) -> dict
    """
    version = get_active_version(db, family_name)
    system_prompt, user_prompt = render_prompt(version, variables)

    # Call LLM
    try:
        llm_result = llm_caller(system_prompt, user_prompt)
    except Exception as e:
        _store_run(db, tenant_id, family_name, version, input_data, None, None,
                   engine_run_id, {"pass": False, "reasons": [str(e)]}, "error", str(e))
        raise HTTPException(status_code=502, detail=f"LLM call failed: {e}")

    output_text = llm_result.get("text", "")
    token_usage = llm_result.get("token_usage")

    # Guardrail check
    guardrail_result = check_guardrails(output_text, version.guardrails or {}, input_data)

    if not guardrail_result["pass"]:
        _store_run(db, tenant_id, family_name, version, input_data, {"text": output_text},
                   token_usage, engine_run_id, guardrail_result, "guardrail_rejected")
        raise HTTPException(
            status_code=422,
            detail={
                "code": "GUARDRAIL_REJECTED",
                "reasons": guardrail_result["reasons"],
                "message": "Model output failed guardrail checks and was rejected.",
            },
        )

    run = _store_run(db, tenant_id, family_name, version, input_data,
                     {"text": output_text}, token_usage, engine_run_id, guardrail_result, "success")

    return {
        "text": output_text,
        "family_name": family_name,
        "version": version.version,
        "model_target": version.model_target,
        "guardrail_result": guardrail_result,
        "token_usage": token_usage,
        "run_id": str(run.id),
    }


def _store_run(
    db: Session,
    tenant_id: UUID,
    family_name: str,
    version: PromptVersion,
    input_data: dict,
    output: Optional[dict],
    token_usage: Optional[dict],
    engine_run_id: Optional[UUID],
    guardrail_result: dict,
    status: str,
    error_message: Optional[str] = None,
) -> PromptRun:
    run = PromptRun(
        tenant_id=tenant_id,
        family_name=family_name,
        version=version.version,
        prompt_version_id=version.id,
        engine_run_id=engine_run_id,
        input=input_data,
        output=output,
        token_usage=token_usage,
        guardrail_result=guardrail_result,
        status=status,
        error_message=error_message,
    )
    db.add(run)
    db.commit()
    return run
