# Architecture Decisions

This document records important architectural decisions.

Do not change these decisions casually.

If a decision needs to change, document the reason and impact before implementation.

---

## ADR-001 — Agent 1 Is a Business Document Intelligence System

### Decision

Agent 1 is designed as a Business Document Intelligence system, not a chatbot.

### Reason

The primary workflow is deterministic document processing followed by AI-assisted retrieval and querying.

---

## ADR-002 — Documents Remain Independent

### Decision

Documents are never automatically merged or aggregated.

### Reason

The user must explicitly control multi-document operations.

### Example

Invoice A, Invoice B and Invoice C remain independent.

A query involving A and C may combine only A and C.

---

## ADR-003 — Deterministic Processing Before AI

### Decision

Parser, Classifier, Extractor and Validator are deterministic.

### Reason

These stages should produce predictable, testable and auditable results.

AI begins after deterministic processing.

---

## ADR-004 — Local Storage

### Decision

Business documents are stored locally.

### Reason

The project prioritizes privacy, security, cost control and workspace isolation.

---

## ADR-005 — ChromaDB Is a Retrieval Index

### Decision

ChromaDB is not the canonical source of documents.

### Reason

Vectors and embeddings are derived data.

The original document remains the source of truth.

---

## ADR-006 — Simple Architecture

### Decision

Prefer simple architecture over premature abstraction.

### Reason

The project is being developed incrementally.

Additional abstractions should only be introduced when a real requirement justifies them.

---

## ADR-007 — Feature Responsibility

### Decision

Features follow the general pattern:

models.py
constants.py
exceptions.py
service.py
tool.py

### Reason

This provides consistent separation of concerns without excessive abstraction.

Additional modules are allowed when justified.

---

## ADR-008 — No Premature Document-Specific Validator Architecture

### Decision

Phase 9 initially uses a single ValidationService.

### Reason

At the current project stage, creating many document-specific validator modules would add structure before there is a demonstrated need.

If document-specific validation complexity grows significantly, the validator can be split later.

---

## ADR-009 — AI Has No Filesystem Access

### Decision

AI receives prepared context only.

### Reason

This prevents arbitrary document access and strengthens workspace/document isolation.

---

## ADR-010 — Backend Enforces Security

### Decision

Security boundaries are enforced by backend components, not by AI instructions.

### Reason

LLMs are not security boundaries.

---

## ADR-011 — Refactor Based on Real Need

### Decision

The project should evolve incrementally.

### Reason

Premature abstraction creates unnecessary complexity.

Refactoring is expected when actual complexity justifies it.