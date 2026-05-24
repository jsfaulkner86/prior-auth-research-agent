"""Structured output schemas for prior authorization justifications."""
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class PriorAuthRecommendation(str, Enum):
    """Allowed final prior authorization recommendations."""

    APPROVE = "approve"
    DENY = "deny"
    PEND = "pend_for_additional_information"


class CriteriaFinding(BaseModel):
    """One payer medical-necessity criterion matched against the request."""

    criterion: str = Field(..., min_length=1)
    status: Literal["met", "not_met", "missing"]
    evidence: str = Field(..., min_length=1)


class PriorAuthJustification(BaseModel):
    """Validated structured output from the decision-summarizer agent."""

    request_id: str = Field(..., min_length=1)
    cpt_code: str = Field(..., min_length=1)
    payer_name: str = Field(..., min_length=1)
    recommendation: PriorAuthRecommendation
    clinical_rationale: str = Field(..., min_length=1)
    criteria: list[CriteriaFinding] = Field(default_factory=list)
    additional_documentation_required: list[str] = Field(default_factory=list)
    denial_risk_codes: list[str] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)

    @field_validator("criteria")
    @classmethod
    def require_criteria_for_final_decisions(
        cls, criteria: list[CriteriaFinding], info
    ) -> list[CriteriaFinding]:
        recommendation = info.data.get("recommendation")
        if recommendation in {
            PriorAuthRecommendation.APPROVE,
            PriorAuthRecommendation.DENY,
        } and not criteria:
            raise ValueError("approve/deny recommendations require criteria findings")
        return criteria

    @field_validator("additional_documentation_required")
    @classmethod
    def require_follow_up_for_pending(
        cls, additional_docs: list[str], info
    ) -> list[str]:
        recommendation = info.data.get("recommendation")
        if recommendation == PriorAuthRecommendation.PEND and not additional_docs:
            raise ValueError("pending recommendations require requested documentation")
        return additional_docs
