# Prior Authorization Research Agent

> **CrewAI + RAG** — Automating the most broken workflow in healthcare

[![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)]()
[![CrewAI](https://img.shields.io/badge/CrewAI-6B46C1?style=flat-square)]()
[![RAG](https://img.shields.io/badge/RAG-Retrieval%20Augmented-orange?style=flat-square)]()
[![Healthcare AI](https://img.shields.io/badge/Healthcare-AI-red?style=flat-square)]()

Built by [The Faulkner Group](https://thefaulknergroupadvisors.com) — directly informed by 14 years of Epic EHR implementation across 12 enterprise health systems.

---

## Problem Statement

Prior authorization kills care delivery. Clinicians and MA staff spend hours manually researching payer-specific medical necessity criteria, drafting justification narratives, and appealing denials — time that delivers zero clinical value. AMA data shows prior auth contributes to care delays in 93% of cases and causes patient abandonment in 82% of cases annually.

This agent automates the research and justification pipeline end-to-end: policy retrieval, criteria matching, denial risk assessment, and structured output ready for submission — with a full append-only audit trail on every decision.

---

## System Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    Auth Request Input                          │
│         patient context · CPT code · diagnosis · payer         │
└──────────────────────────────┬─────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────┐
│              CrewAI Sequential Agent Pipeline                   │
│                                                                 │
│  ┌─────────────────────┐                                          │
│  │  Policy Retriever Agent  │                                  │
│  │  RAG over payer policy   │                                  │
│  │  docs · vector search    │                                  │
│  │  · rerank · compression  │                                  │
│  └───────────┬───────────┘                                  │
│               │ medical necessity criteria list                  │
│               ▼                                                 │
│  ┌─────────────────────┐                                          │
│  │  Criteria Matcher Agent  │                                  │
│  │  clinical notes vs.      │                                  │
│  │  policy criteria ·       │                                  │
│  │  met/not-met checklist   │                                  │
│  └───────────┬───────────┘                                  │
│               │ criteria match results + gaps                    │
│               ▼                                                 │
│  ┌─────────────────────┐                                          │
│  │ Decision Summarizer      │                                  │
│  │ Agent                    │                                  │
│  │ drafts justification ·   │                                  │
│  │ flags denial risk codes  │                                  │
│  │ Approve/Deny/Pend output │                                  │
│  └───────────┬───────────┘                                  │
│               │                                                 │
│               ▼                                                 │
│  ┌─────────────────────┐                                          │
│  │  Confidence Check        │                                  │
│  └─────────┬────────────┘                                  │
│           │ high           │ low                               │
│           ▼                ▼                                   │
│  ✅ Auth Request Ready   🔁 Human Review Flagged                  │
└─────────────────────────────────────────────────────────────────┘
          │ Append-only audit log on every agent transition
          ▼
┌─────────────────────────────────────────────────────────────────┐
│  PostgreSQL: prior_auth_audit_log (append-only)                  │
└─────────────────────────────────────────────────────────────────┘
```

### Core Design Principles

- **Sequential crew, not parallel** — each agent’s output is the next agent’s input. Policy retrieval must complete before criteria matching; criteria results must exist before denial risk assessment.
- **RAG over payer policy documents** — the Policy Retriever Agent queries a vector store of ingested payer LCD/NCD documents rather than relying on LLM training data, which is stale by nature.
- **Human review as a first-class output** — low confidence does not produce a silent failure. It produces a `HUMAN_REVIEW_FLAGGED` event and surfaces the request for clinical escalation.
- **Denial risk is preemptive** — the Decision Summarizer drafts rebuttal language for likely denial codes *before* submission, not after denial.

---

## Repository Structure

```
prior-auth-research-agent/
├── app.py                          # Streamlit UI for interactive auth request submission
├── main.py                         # CrewAI crew definition and kickoff entry point
├── requirements.txt
├── .env.example
│
├── audit/
│   ├── models.py                   # PriorAuthAuditEvent model (10 event types)
│   ├── logger.py                   # Append-only asyncpg writer — never raises
│   ├── queries.py                  # Denial risk summary, payer approval rates, CPT volume
│   └── migrations/
│       └── 001_create_prior_auth_audit_log.sql
│
└── tests/
    └── test_audit.py
```

---

## Technology Stack

| Layer | Technology | Rationale |
|---|---|---|
| **Agent Orchestration** | CrewAI | Role-based crew pattern — each agent has a distinct domain responsibility |
| **Retrieval** | LangChain RAG + vector store | Policy documents are too large and too frequently updated to rely on LLM training data |
| **LLM** | OpenAI GPT-4o | Structured justification drafting + criteria assessment |
| **Audit Store** | PostgreSQL + asyncpg | Append-only event log with denial code array indexing |
| **UI** | Streamlit | Rapid clinical-facing interface for request submission and output review |
| **Language** | Python 3.11+ | Async-native; type hints throughout |

---

## Prior Auth Workflow Context

### The X12 278 Transaction Lifecycle

Prior auth in production health systems follows the X12 278 EDI standard. This agent addresses steps 5–7:

| Step | Transaction | Description | Agent Coverage |
|---|---|---|---|
| 1 | X12 270 | Eligibility inquiry | ❌ Upstream |
| 2 | X12 271 | Eligibility response | ❌ Upstream |
| 3 | X12 278 Request | Auth request submission | 📋 Roadmap |
| 4 | X12 278 Response | Payer approval/denial | 📋 Roadmap |
| 5 | Policy Research | Medical necessity criteria lookup | ✅ Policy Retriever Agent |
| 6 | Clinical Justification | Narrative drafting against criteria | ✅ Criteria Matcher Agent |
| 7 | Decision Summary | Approve / Deny / Pend rationale | ✅ Decision Summarizer Agent |
| 8 | Peer-to-Peer | Clinical escalation for denials | 📋 Roadmap |
| 9 | Appeal | Formal denial appeal submission | 📋 Roadmap |

### Denial Codes Addressed

| Code | Meaning | Agent Response |
|---|---|---|
| `CO-4` | Not authorized | Policy gaps flagged by Policy Retriever |
| `CO-50` | Not medically necessary | Clinical justification narrative built against necessity criteria |
| `CO-97` | CPT bundling conflict | CPT bundling flag in criteria match |
| `CO-167` | Diagnosis not covered | ICD-10 alignment check |
| `PR-204` | Not covered by plan | Coverage verification flag |

---

## Audit Event Lifecycle

```
auth_request_received
    └── policy_research_started
            └── policy_research_completed
                    └── criteria_match_started
                            └── criteria_match_completed
                                    └── denial_risk_assessed
                                            └── justification_drafted
                                                    └── auth_request_ready
                                                    └── human_review_flagged
                                                    └── auth_request_failed
```

---

## Compliance Posture

- **HIPAA:** `patient_id` stored as de-identified token. Never log raw MRN, name, or DOB. Connect live Epic FHIR context only through a system-to-system SMART-on-FHIR integration with a BAA in place.
- **Audit Trail:** `prior_auth_audit_log` is append-only. Satisfies CMS audit requirements for automated PA tools under the 2024 CMS Interoperability and Prior Authorization Rule (CMS-0057-F).
- **Denial Transparency:** Every `auth_request_ready` event records `denial_risk_codes[]` — the specific codes the agent preemptively addressed. This provides documented due diligence in any payer dispute.

---

## Known Failure Modes

| Failure Mode | Impact | Mitigation |
|---|---|---|
| Stale payer policy documents in vector store | Criteria mismatch — incorrect justification | Schedule nightly policy document refresh pipeline; version-stamp embeddings |
| LLM hallucinates CPT criteria | False-positive criteria-met determination | Retrieval-grounded output only — LLM must cite retrieved chunks, not training data |
| Payer changes criteria between request and response | Criteria valid at submission, invalid at review | Log `policy_research_completed` timestamp; flag if payer policy version changed |
| Low confidence on rare CPT codes | Excessive human review flags | Expand policy corpus for rare procedures; fall back to human review explicitly |

---

## Local Development

```bash
git clone https://github.com/jsfaulkner86/prior-auth-research-agent
cd prior-auth-research-agent
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Run database migration
psql $DATABASE_URL -f audit/migrations/001_create_prior_auth_audit_log.sql

# Run Streamlit UI
streamlit run app.py

# Or run headless
python main.py

# Run tests
pytest tests/ -v
```

---

## What's Next

- Payer-specific policy document ingestion pipeline with version tracking
- X12 278 submission integration
- Appeals agent for denied authorizations
- Epic FHIR integration for real-time patient context
- Peer-to-peer escalation workflow

---

<img width="1433" height="729" alt="Prior Auth Agent UI" src="https://github.com/user-attachments/assets/7a6ae2d3-c4ca-498d-9f9c-2558072f71d9" />
<img width="1428" height="523" alt="Prior Auth Agent Output" src="https://github.com/user-attachments/assets/d0d7dcd0-3f1e-462c-9b0a-eb2eff175f6c" />

---

*Part of The Faulkner Group’s healthcare agentic AI portfolio. See all projects at [github.com/jsfaulkner86](https://github.com/jsfaulkner86)*
