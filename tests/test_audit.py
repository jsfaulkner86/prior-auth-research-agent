"""Tests for the prior auth audit layer."""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from audit.models import PriorAuthAuditEvent, PriorAuthAuditEventType
from audit.logger import PriorAuthAuditLogger


def test_audit_event_model():
    event = PriorAuthAuditEvent(
        event_type=PriorAuthAuditEventType.AUTH_REQUEST_READY,
        request_id="PA-001",
        patient_id="P-TOKEN-001",
        cpt_code="99213",
        diagnosis_code="Z00.00",
        payer_name="Aetna",
        criteria_met=True,
        denial_risk_codes=["CO-50"],
        confidence=0.88,
    )
    assert event.id is not None
    assert isinstance(event.created_at, datetime)
    assert event.criteria_met is True
    assert "CO-50" in event.denial_risk_codes


@pytest.mark.asyncio
async def test_logger_never_raises_without_pool():
    logger = PriorAuthAuditLogger(dsn="postgresql://test")
    logger._pool = None
    await logger.log(PriorAuthAuditEvent(
        event_type=PriorAuthAuditEventType.AUTH_REQUEST_FAILED,
        request_id="PA-FAIL",
        error_detail="Test failure",
    ))


@pytest.mark.asyncio
async def test_logger_writes_event():
    logger = PriorAuthAuditLogger(dsn="postgresql://test")
    mock_conn = AsyncMock()
    mock_pool = AsyncMock()
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)
    logger._pool = mock_pool

    await logger.log_request_ready(
        request_id="PA-001",
        patient_id="P-001",
        cpt_code="99213",
        diagnosis_code="Z00.00",
        payer_name="Aetna",
        criteria_met=True,
        denial_risk_codes=[],
        confidence=0.91,
    )
    mock_conn.execute.assert_called_once()
