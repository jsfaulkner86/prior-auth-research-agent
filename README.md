# Prior Authorization Research Agent

> **CrewAI + RAG** — Automating the most broken workflow in healthcare

[![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)]()
[![CrewAI](https://img.shields.io/badge/CrewAI-6B46C1?style=flat-square)]()
[![RAG](https://img.shields.io/badge/RAG-Retrieval%20Augmented-orange?style=flat-square)]()
[![Healthcare AI](https://img.shields.io/badge/Healthcare-AI-red?style=flat-square)]()

## The Problem

Prior authorization kills care. Clinicians spend hours manually researching payer policies, submitting requests, and appealing denials — time that should be spent with patients. This agent automates that research pipeline end-to-end.

## What It Does

A multi-agent system built with CrewAI that:
- Researches payer-specific prior auth requirements using RAG over policy documents
- Drafts clinical justification narratives based on patient context
- Identifies likely denial reasons and preemptively addresses them
- Returns a structured authorization request ready for submission

```mermaid
flowchart TD
    A[Prior Auth Request\npatient context · CPT code\ndiagnosis · payer] --> B[Policy Research Agent\nRAG over payer policy docs\nvector search · rerank]

    B -->|Policy requirements retrieved| C[Clinical Justification Agent\ndrafts narrative\npatient context + policy match]

    C -->|Draft justification| D[Denial Risk Agent\nidentifies likely denial reasons\nCO-4 · CO-97 · CO-50\npreemptive rebuttal drafted]

    D -->|Risk-adjusted narrative| E[Output Assembler\nstructured auth request\nCPT · diagnosis · justification\ndenial rebuttals]

    E --> F{Confidence Check}
    F -->|High confidence| G[✅ Auth Request Ready\nfor submission]
    F -->|Low confidence| H[🔁 Human Review Flag\nescalate to clinician]

    style G fill:#22c55e,color:#fff
    style H fill:#f59e0b,color:#fff
    style E fill:#6B46C1,color:#fff
```

## Tech Stack

| Layer | Technology |
|---|---|
| Agent Orchestration | CrewAI |
| Retrieval | RAG (LangChain + vector store) |
| LLM | OpenAI GPT-4 |
| Language | Python 3.11+ |

## Getting Started

```bash
git clone https://github.com/jsfaulkner86/prior-auth-research-agent
cd prior-auth-research-agent
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Add your API keys
python main.py
```

## Environment Variables

Create a `.env` file (never commit this):
```
OPENAI_API_KEY=your_key_here
```

## Background

Built by [John Faulkner](https://linkedin.com/in/johnathonfaulkner), Agentic AI Architect and founder of [The Faulkner Group](https://thefaulknergroupadvisors.com). This project draws directly from 14 years of Epic EHR implementation experience across 12 enterprise health systems.

## What's Next
- Payer-specific policy document ingestion pipeline
- Appeals agent for denied authorizations
- Epic FHIR integration for real patient context

---
*Part of a portfolio of healthcare agentic AI systems. See all projects at [github.com/jsfaulkner86](https://github.com/jsfaulkner86)*
