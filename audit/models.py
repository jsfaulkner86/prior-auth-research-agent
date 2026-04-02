"""Audit event models for the Prior Authorization Research Agent."""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class PriorAuthAuditEventType(str, Enum):
    AUTH_REQUEST_RECEIVED = "auth_request_received"
    POLICY_RESEARCH_STARTED = "policy_research_started"
    POLICY_RESEARCH_COMPLETED = "policy_research_completed"
    CRITERIA_MATCH_STARTED = "criteria_match_started"
    CRITERIA_MATCH_COMPLETED = "criteria_match_completed"
    DENIAL_RISK_ASSESSED = "denial_risk_assessed"
    JUSTIFICATION_DRAFTED = "justification_drafted"
    HUMAN_REVIEW_FLAGGED = "human_review_flagged"
    AUTH_REQUEST_READY = "auth_request_ready"
    AUTH_REQUEST_FAILED = "auth_request_failed"


class PriorAuthAuditEvent(BaseModel):
    """Immutable audit record for a single prior auth workflow event."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    event_type: PriorAuthAuditEventType
    request_id: Optional[str] = None          # internal request tracking ID
    patient_id: Optional[str] = None          # de-identified token
    cpt_code: Optional[str] = None
    diagnosis_code: Optional[str] = None      # ICD-10
    payer_name: Optional[str] = None
    crew_agent: Optional[str] = None          # which CrewAI agent fired this event
    criteria_met: Optional[bool] = None
    denial_risk_codes: Optional[list[str]] = None  # e.g. ["CO-50", "CO-4"]
    confidence: Optional[float] = None
    requires_human_review: bool = False
    error_detail: Optional[str] = None
    metadata: Optional[dict] = None


AUDIT_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS prior_auth_audit_log (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type           TEXT NOT NULL,
    request_id           TEXT,
    patient_id           TEXT,
    cpt_code             TEXT,
    diagnosis_code       TEXT,
    payer_name           TEXT,
    crew_agent           TEXT,
    criteria_met         BOOLEAN,
    denial_risk_codes    TEXT[],
    confidence           NUMERIC(5,4),
    requires_human_review BOOLEAN NOT NULL DEFAULT FALSE,
    error_detail         TEXT,
    metadata             JSONB
);

CREATE INDEX IF NOT EXISTS idx_pa_audit_event_type  ON prior_auth_audit_log (event_type);
CREATE INDEX IF NOT EXISTS idx_pa_audit_request_id  ON prior_auth_audit_log (request_id);
CREATE INDEX IF NOT EXISTS idx_pa_audit_payer       ON prior_auth_audit_log (payer_name);
CREATE INDEX IF NOT EXISTS idx_pa_audit_cpt         ON prior_auth_audit_log (cpt_code);
CREATE INDEX IF NOT EXISTS idx_pa_audit_created_at  ON prior_auth_audit_log (created_at DESC);

COMMENT ON TABLE prior_auth_audit_log IS
    'Immutable append-only audit trail for all prior authorization research decisions. Never UPDATE or DELETE rows.';
"""
