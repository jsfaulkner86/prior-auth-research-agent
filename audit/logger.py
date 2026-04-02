"""Append-only audit logger for prior authorization research events."""
import os
import json
import logging
import asyncpg
from typing import Optional
from .models import PriorAuthAuditEvent, PriorAuthAuditEventType

logger = logging.getLogger(__name__)


class PriorAuthAuditLogger:
    """
    Append-only audit logger backed by PostgreSQL.
    Never raises — failed audit writes must not interrupt the auth research pipeline.
    """

    def __init__(self, dsn: Optional[str] = None) -> None:
        self.dsn = dsn or os.getenv("DATABASE_URL", "")
        self._pool: Optional[asyncpg.Pool] = None

    async def init(self) -> None:
        self._pool = await asyncpg.create_pool(self.dsn, min_size=1, max_size=5)

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()

    async def log(self, event: PriorAuthAuditEvent) -> None:
        if not self._pool:
            logger.warning("PriorAuthAuditLogger not initialized — event dropped: %s", event.event_type)
            return
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO prior_auth_audit_log (
                        id, created_at, event_type, request_id, patient_id,
                        cpt_code, diagnosis_code, payer_name, crew_agent,
                        criteria_met, denial_risk_codes, confidence,
                        requires_human_review, error_detail, metadata
                    ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15)
                    """,
                    event.id, event.created_at, event.event_type.value,
                    event.request_id, event.patient_id, event.cpt_code,
                    event.diagnosis_code, event.payer_name, event.crew_agent,
                    event.criteria_met, event.denial_risk_codes,
                    event.confidence, event.requires_human_review,
                    event.error_detail,
                    json.dumps(event.metadata) if event.metadata else None,
                )
        except Exception as e:
            logger.error("PriorAuth audit write failed [%s]: %s", event.request_id, e)

    async def log_request_ready(
        self,
        request_id: str,
        patient_id: str,
        cpt_code: str,
        diagnosis_code: str,
        payer_name: str,
        criteria_met: bool,
        denial_risk_codes: list[str],
        confidence: float,
    ) -> None:
        await self.log(PriorAuthAuditEvent(
            event_type=PriorAuthAuditEventType.AUTH_REQUEST_READY,
            request_id=request_id,
            patient_id=patient_id,
            cpt_code=cpt_code,
            diagnosis_code=diagnosis_code,
            payer_name=payer_name,
            criteria_met=criteria_met,
            denial_risk_codes=denial_risk_codes,
            confidence=confidence,
        ))

    async def log_human_review_flagged(
        self,
        request_id: str,
        reason: str,
        cpt_code: Optional[str] = None,
        payer_name: Optional[str] = None,
    ) -> None:
        await self.log(PriorAuthAuditEvent(
            event_type=PriorAuthAuditEventType.HUMAN_REVIEW_FLAGGED,
            request_id=request_id,
            cpt_code=cpt_code,
            payer_name=payer_name,
            requires_human_review=True,
            metadata={"flag_reason": reason},
        ))


audit_logger = PriorAuthAuditLogger()
