"""Tests for prior authorization justification schemas."""

import pytest
from pydantic import ValidationError
from unittest.mock import Mock

from schemas import CriteriaFinding, PriorAuthJustification, PriorAuthRecommendation


def complete_justification(**overrides):
    data = {
        "request_id": "PA-TEST-001",
        "cpt_code": "27447",
        "payer_name": "Example Health Plan",
        "recommendation": PriorAuthRecommendation.APPROVE,
        "clinical_rationale": "Documented conservative therapy and imaging support medical necessity.",
        "criteria": [
            {
                "criterion": "Radiographic evidence of advanced osteoarthritis",
                "status": "met",
                "evidence": "X-ray shows grade IV joint space narrowing.",
            },
            {
                "criterion": "Conservative treatment attempted",
                "status": "met",
                "evidence": "Six months of physical therapy and NSAIDs were tried.",
            },
        ],
        "additional_documentation_required": [],
        "denial_risk_codes": [],
        "confidence": 0.91,
    }
    data.update(overrides)
    return PriorAuthJustification.model_validate(data)


def test_complete_justification_output_validates_required_fields():
    output = complete_justification()

    assert output.request_id == "PA-TEST-001"
    assert output.cpt_code == "27447"
    assert output.payer_name == "Example Health Plan"
    assert output.recommendation is PriorAuthRecommendation.APPROVE
    assert output.criteria[0].status == "met"


def test_missing_clinical_criteria_rejected_for_final_recommendation():
    with pytest.raises(ValidationError, match="criteria findings"):
        complete_justification(criteria=[])


def test_pending_incomplete_request_requires_follow_up_documentation():
    with pytest.raises(ValidationError, match="requested documentation"):
        complete_justification(
            recommendation=PriorAuthRecommendation.PEND,
            criteria=[],
            additional_documentation_required=[],
        )


def test_pending_request_allows_missing_criteria_when_follow_up_is_present():
    output = complete_justification(
        recommendation="pend_for_additional_information",
        criteria=[],
        additional_documentation_required=["Upload the most recent physical therapy notes."],
        confidence=0.62,
    )

    assert output.recommendation is PriorAuthRecommendation.PEND
    assert output.additional_documentation_required == [
        "Upload the most recent physical therapy notes."
    ]


def test_unsupported_payer_empty_string_is_rejected():
    with pytest.raises(ValidationError):
        complete_justification(payer_name="")


def test_confidence_must_be_between_zero_and_one():
    with pytest.raises(ValidationError):
        complete_justification(confidence=1.25)


def test_llm_response_can_be_mocked_and_validated_without_api_key():
    mock_llm = Mock(
        return_value={
            "request_id": "PA-MOCK-001",
            "cpt_code": "70553",
            "payer_name": "Example Health Plan",
            "recommendation": "deny",
            "clinical_rationale": "The submitted note lacks documented neurological deficits.",
            "criteria": [
                CriteriaFinding(
                    criterion="Focal neurological deficit documented",
                    status="missing",
                    evidence="No neurological exam findings were included.",
                ).model_dump()
            ],
            "additional_documentation_required": ["Provide neurological exam findings."],
            "denial_risk_codes": ["CO-50"],
            "confidence": 0.74,
        }
    )

    output = PriorAuthJustification.model_validate(mock_llm())

    mock_llm.assert_called_once_with()
    assert output.recommendation is PriorAuthRecommendation.DENY
    assert output.denial_risk_codes == ["CO-50"]
