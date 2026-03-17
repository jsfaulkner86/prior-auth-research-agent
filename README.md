# Prior Authorization Multi-Agent System

Architecture: 3-agent CrewAI crew automating the most broken workflow in healthcare.

## The Problem
Prior authorization costs the U.S. healthcare system $13B annually in administrative burden. I've watched it delay care and destroy clinical workflows for 14 years as an Epic EHR Architect across 12 enterprise health systems. This is the agentic AI version of what I know needs to exist.

## Agent Architecture
| Agent | Role | Tools |
|---|---|---|
| Policy Retriever | Pulls payer policy based on CPT code | RAG over payer PDFs |
| Clinical Criteria Matcher | Compares clinical notes to approval criteria | LLM + structured data |
| Decision Summarizer | Generates approval/denial rationale | LLM output formatting |

## Tech Stack
- Framework: CrewAI
- LLM: OpenAI GPT-4 / Claude
- Data: Mock payer policy PDFs, sample clinical notes
- Compliance: HIPAA-aware design, no real PHI used

## Why This Architecture
CrewAI's role-based agent model mirrors how actual prior auth teams are staffed — making it the right framework for stakeholder communication and explainability.

## Status
🔨 In Progress — target completion April 2026
Part of Harvard Data Science Initiative Agentic AI coursework
