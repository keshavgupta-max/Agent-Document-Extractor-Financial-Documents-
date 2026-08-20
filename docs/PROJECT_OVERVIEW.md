# AI B2B Accountant & Sales Management Platform

## 1. Project Identity

This project is an AI-powered Business Document Intelligence Platform.

It is NOT a chatbot.

It is NOT a general AI assistant.

The platform is designed to process business documents, extract structured information, validate that information, create searchable representations, and eventually provide document-grounded AI answers.

The platform will eventually contain multiple independent AI agents.

---

## 2. Long-Term Platform

The platform will eventually contain:

### Agent 1 — Business Document Intelligence

Current development focus.

Responsibilities:

- Business document ingestion
- Secure document storage
- Document parsing
- Document classification
- Structured data extraction
- Validation
- Embedding preparation
- Embedding generation
- Vector indexing
- Document retrieval
- Document-grounded AI querying

### Agent 2 — Accounting Intelligence

Future agent.

Not part of the current implementation.

### Agent 3 — Sales Intelligence

Future agent.

Not part of the current implementation.

### Agent 4 — Business Insights / Predictions

Future agent.

Not part of the current implementation.

Each agent will have its own backend.

A future orchestration layer will allow the agents to communicate.

---

## 3. Current Scope

The current project focuses ONLY on Agent 1.

Do not implement functionality belonging to Agent 2, Agent 3, or Agent 4.

---

## 4. Core Principle

Business documents remain independent.

If a user uploads:

- Invoice A
- Invoice B
- Invoice C

the system must not automatically combine, aggregate, or compare them.

They remain independent.

If the user explicitly asks:

> What is the total revenue of Invoice A and Invoice C?

only the selected documents may be combined for that operation.

The user controls document combination.

---

## 5. AI Philosophy

Deterministic processing must happen before AI.

The current processing philosophy is:

Upload
→ Storage
→ Parser
→ Classifier
→ Extractor
→ Validator
→ Embedding Preparation
→ Embedding Generation
→ Vector Database
→ Retrieval
→ AI Query

AI must not replace deterministic processing where deterministic processing is sufficient.

---

## 6. Technology Principles

The project uses:

- Python 3.12+
- Pydantic v2
- FastAPI where HTTP APIs are required
- Strong typing
- Local storage
- ChromaDB for vector indexing
- Gemini for future AI/embedding functionality

The implementation should remain:

- Simple
- Readable
- Maintainable
- Production inspired
- Secure
- Strongly typed

Avoid unnecessary abstraction and overengineering.

---

## 7. Current Development Status

- Phase 1 — Runtime Foundation
- Phase 2 — Tool Framework
- Phase 3 — Agent State
- Phase 4 — Upload API and Upload Tool
- Phase 5 — Storage Manager
- Phase 6 — Document Parsing Engine
- Phase 7 — Business Document Classification
- Phase 8 — Structured Data Extraction
- Phase 9 — Document Validation
- Phase 11 — Embedding Generation
- Phase 12 — Vector Storage
- Phase 13 — Retrieval
- Phase 14 — AI Query Engine
- Phase 15 — Query API
- Phase 16 — Security Hardening
- Phase 17 — Agent 1 Integration
- Phase 18 — Testing and Evaluation
- Phase 19 — Observability
- Phase 20 — Production Hardening