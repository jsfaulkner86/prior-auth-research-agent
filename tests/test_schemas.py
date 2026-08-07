"""Tests for structured prior authorization justification schemas."""
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from schemas import (
    CriteriaStatus,
    PriorAuthJustificationOutput,
    PriorAuthRecommendation,
    validate_prior_auth_justification,
)


def valid_justification_payload() -> dict:
    return {
        "cpt_code": "27447",
        "diagnosis_code": "M17.11",
        "payer_name": "Synthetic Health Plan",
        "recommendation": "APPROVE",
        "clinical_rationale": "Synthetic notes document failed conservative therapy and severe functional limitation.",
        "criteria": [
            {
                "description": "Radiographic evidence of advanced joint disease",
                "status": "MET",
                "evidence": "Synthetic x-ray summary notes grade IV joint space narrowing.",
            },
            {
                "description": "Conservative therapy attempted before surgery",
                "status": "MET",
                "evidence": "Synthetic notes include physical therapy, NSAIDs, and injections.",
            },
        ],
        "additional_documentation_required": [],
        "denial_risk_codes": [],
        "requires_human_review": False,
        "confidence": 0.91,
    }


def test_valid_prior_auth_justification_output_populates_required_fields():
    output = PriorAuthJustificationOutput.model_validate(valid_justification_payload())

    assert output.cpt_code == "27447"
    assert output.diagnosis_code == "M17.11"
    assert output.payer_name == "Synthetic Health Plan"
    assert output.recommendation == PriorAuthRecommendation.APPROVE
    assert output.criteria[0].status == CriteriaStatus.MET


def test_validation_isolated_from_llm_calls():
    llm_client = Mock()
    llm_client.generate.return_value = valid_justification_payload()

    output = validate_prior_auth_justification(llm_client.generate())

    llm_client.generate.assert_called_once()
    assert output.confidence == 0.91


def test_missing_clinical_criteria_are_rejected():
    payload = valid_justification_payload()
    payload["criteria"] = []

    with pytest.raises(ValidationError, match="criteria"):
        PriorAuthJustificationOutput.model_validate(payload)


def test_unmet_criteria_require_documentation_gap():
    payload = valid_justification_payload()
    payload["recommendation"] = "PEND_FOR_ADDITIONAL_INFORMATION"
    payload["criteria"][0] = {
        "description": "Recent conservative therapy documentation",
        "status": "NOT_MET",
    }

    with pytest.raises(ValidationError, match="documentation_gap"):
        PriorAuthJustificationOutput.model_validate(payload)


def test_unsupported_payer_requires_human_review_and_cannot_approve():
    payload = valid_justification_payload()
    payload["payer_name"] = "Unsupported Synthetic Payer"
    payload["payer_supported"] = False

    with pytest.raises(ValidationError, match="unsupported payers"):
        PriorAuthJustificationOutput.model_validate(payload)

    payload["recommendation"] = "PEND_FOR_ADDITIONAL_INFORMATION"
    with pytest.raises(ValidationError, match="human review"):
        PriorAuthJustificationOutput.model_validate(payload)

    payload["requires_human_review"] = True
    output = PriorAuthJustificationOutput.model_validate(payload)
    assert output.requires_human_review is True


def test_incomplete_request_missing_required_fields_is_rejected():
    payload = valid_justification_payload()
    del payload["diagnosis_code"]

    with pytest.raises(ValidationError, match="diagnosis_code"):
        PriorAuthJustificationOutput.model_validate(payload)


def test_approval_rejects_missing_or_unknown_criteria():
    payload = valid_justification_payload()
    payload["criteria"][1] = {
        "description": "Payer policy explicitly supports the requested CPT",
        "status": "UNKNOWN",
        "documentation_gap": "Synthetic payer policy was unavailable.",
    }

    with pytest.raises(ValidationError, match="approval requires all criteria"):
        PriorAuthJustificationOutput.model_validate(payload)
