"""Read-side analytics for prior authorization audit data."""
import os
import asyncpg
from datetime import datetime, timedelta
from typing import Optional


class PriorAuthAuditQueryService:

    def __init__(self, dsn: Optional[str] = None) -> None:
        self.dsn = dsn or os.getenv("DATABASE_URL", "")
        self._pool: Optional[asyncpg.Pool] = None

    async def init(self) -> None:
        self._pool = await asyncpg.create_pool(self.dsn, min_size=1, max_size=3)

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()

    async def get_request_trail(self, request_id: str) -> list[dict]:
        """Full event trail for a single prior auth request."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM prior_auth_audit_log WHERE request_id=$1 ORDER BY created_at ASC",
                request_id,
            )
            return [dict(r) for r in rows]

    async def get_denial_risk_summary(
        self, since: Optional[datetime] = None
    ) -> list[dict]:
        """Most frequent denial risk codes across all processed requests."""
        since = since or (datetime.utcnow() - timedelta(days=30))
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT code, COUNT(*) AS frequency
                FROM prior_auth_audit_log,
                     UNNEST(denial_risk_codes) AS code
                WHERE created_at >= $1
                GROUP BY code ORDER BY frequency DESC
                """,
                since,
            )
            return [dict(r) for r in rows]

    async def get_payer_approval_rate(
        self, since: Optional[datetime] = None
    ) -> list[dict]:
        """Criteria-met rate by payer — identifies payers with toughest requirements."""
        since = since or (datetime.utcnow() - timedelta(days=30))
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT payer_name,
                       COUNT(*) AS total,
                       COUNT(*) FILTER (WHERE criteria_met = TRUE) AS criteria_met_count,
                       ROUND(COUNT(*) FILTER (WHERE criteria_met = TRUE) * 100.0 / COUNT(*), 2) AS approval_rate_pct
                FROM prior_auth_audit_log
                WHERE event_type = 'auth_request_ready' AND created_at >= $1
                GROUP BY payer_name ORDER BY approval_rate_pct ASC
                """,
                since,
            )
            return [dict(r) for r in rows]

    async def get_cpt_volume(
        self, since: Optional[datetime] = None
    ) -> list[dict]:
        """Top CPT codes processed — use for policy document ingestion prioritization."""
        since = since or (datetime.utcnow() - timedelta(days=30))
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT cpt_code, COUNT(*) AS volume
                FROM prior_auth_audit_log
                WHERE event_type = 'auth_request_received' AND created_at >= $1
                GROUP BY cpt_code ORDER BY volume DESC LIMIT 25
                """,
                since,
            )
            return [dict(r) for r in rows]

    async def get_pipeline_summary(
        self, since: Optional[datetime] = None
    ) -> dict:
        """Aggregate pipeline metrics: volume, criteria met rate, human review rate."""
        since = since or (datetime.utcnow() - timedelta(days=30))
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) FILTER (WHERE event_type='auth_request_received')  AS total_received,
                    COUNT(*) FILTER (WHERE event_type='auth_request_ready')     AS total_ready,
                    COUNT(*) FILTER (WHERE event_type='human_review_flagged')   AS flagged_for_review,
                    COUNT(*) FILTER (WHERE event_type='auth_request_failed')    AS failed,
                    ROUND(AVG(confidence) FILTER (WHERE event_type='auth_request_ready'), 4) AS avg_confidence
                FROM prior_auth_audit_log WHERE created_at >= $1
                """,
                since,
            )
            return dict(row)
