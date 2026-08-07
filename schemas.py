"""Pydantic schemas for structured prior authorization outputs."""
from enum import Enum
from typing import Any, Mapping, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PriorAuthRecommendation(str, Enum):
    """Allowed prior authorization recommendations."""

    APPROVE = "APPROVE"
    DENY = "DENY"
    PEND_FOR_ADDITIONAL_INFORMATION = "PEND_FOR_ADDITIONAL_INFORMATION"


class CriteriaStatus(str, Enum):
    """Allowed payer criteria match states."""

    MET = "MET"
    NOT_MET = "NOT_MET"
    UNKNOWN = "UNKNOWN"


class CriteriaAssessment(BaseModel):
    """A single medical necessity criterion and how it matched the request."""

    model_config = ConfigDict(str_strip_whitespace=True)

    description: str = Field(min_length=1)
    status: CriteriaStatus
    evidence: Optional[str] = None
    documentation_gap: Optional[str] = None

    @model_validator(mode="after")
    def require_gap_for_missing_or_unknown_criteria(self) -> "CriteriaAssessment":
        if self.status in {CriteriaStatus.NOT_MET, CriteriaStatus.UNKNOWN} and not self.documentation_gap:
            raise ValueError("documentation_gap is required when criteria are not met or unknown")
        return self


class PriorAuthJustificationOutput(BaseModel):
    """Validated output from the prior authorization decision summarizer."""

    model_config = ConfigDict(str_strip_whitespace=True)

    cpt_code: str = Field(min_length=1)
    diagnosis_code: str = Field(min_length=1)
    payer_name: str = Field(min_length=1)
    payer_supported: bool = True
    recommendation: PriorAuthRecommendation
    clinical_rationale: str = Field(min_length=1)
    criteria: list[CriteriaAssessment] = Field(min_length=1)
    additional_documentation_required: list[str] = Field(default_factory=list)
    denial_risk_codes: list[str] = Field(default_factory=list)
    requires_human_review: bool = False
    confidence: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def validate_decision_safety(self) -> "PriorAuthJustificationOutput":
        if not self.payer_supported:
            if self.recommendation == PriorAuthRecommendation.APPROVE:
                raise ValueError("unsupported payers cannot receive an approval recommendation")
            if not self.requires_human_review:
                raise ValueError("unsupported payers must be flagged for human review")

        missing_criteria = [
            criterion
            for criterion in self.criteria
            if criterion.status in {CriteriaStatus.NOT_MET, CriteriaStatus.UNKNOWN}
        ]
        if missing_criteria and self.recommendation == PriorAuthRecommendation.APPROVE:
            raise ValueError("approval requires all criteria to be met")

        return self


def validate_prior_auth_justification(payload: Mapping[str, Any]) -> PriorAuthJustificationOutput:
    """Validate a structured LLM response without making any model calls."""

    return PriorAuthJustificationOutput.model_validate(payload)
