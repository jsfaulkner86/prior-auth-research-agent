-- Migration: 001_create_prior_auth_audit_log
-- Append-only audit trail for prior authorization research decisions.
-- Safe to re-run (IF NOT EXISTS guards).

CREATE TABLE IF NOT EXISTS prior_auth_audit_log (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type           TEXT NOT NULL,
    request_id           TEXT,           -- internal tracking ID per auth request
    patient_id           TEXT,           -- de-identified token; never store raw MRN
    cpt_code             TEXT,           -- CPT procedure code
    diagnosis_code       TEXT,           -- ICD-10 diagnosis code
    payer_name           TEXT,
    crew_agent           TEXT,           -- CrewAI agent that generated this event
    criteria_met         BOOLEAN,        -- TRUE = medical necessity criteria satisfied
    denial_risk_codes    TEXT[],         -- e.g. {"CO-50","CO-4"}
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
    'Immutable append-only audit trail for all prior authorization research pipeline events. Never UPDATE or DELETE rows.';
