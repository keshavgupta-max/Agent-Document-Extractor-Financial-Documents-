# Agent 1 Architecture

## 1. Architectural Philosophy

The system follows a layered architecture.

The architecture prioritizes:

1. Maintainability
2. Readability
3. Security
4. Clear responsibility
5. Testability
6. Future extensibility
7. Simplicity

Do not introduce complexity without a demonstrated requirement.

---

## 2. Core Architecture

The primary execution architecture is:

HTTP Request
↓
API
↓
Runtime
↓
AgentState
↓
Tool Executor
↓
Tool
↓
Service
↓
Feature Modules
↓
ToolResult

---

## 3. Layer Responsibilities

### API

Responsible for:

- HTTP requests
- HTTP responses
- Request validation
- Authentication/context handling where applicable
- Calling the runtime

API must NOT contain business logic.

---

### Runtime

Responsible for:

- Executing agent operations
- Managing tool execution
- Coordinating AgentState and tools

Runtime must not contain feature-specific business rules.

---

### AgentState

Contains execution context required by the agent.

It provides controlled state between tools.

Do not use arbitrary global state.

---

### Tool Executor

Responsible for invoking tools through the established tool framework.

---

### Tool

Tools are the integration boundary between the runtime and feature services.

A tool should:

- Receive AgentState and validated input where required
- Call the appropriate service
- Convert the result into ToolResult
- Handle tool-level errors appropriately

A tool should not contain large amounts of business logic.

---

### Service

Services contain feature-specific business logic.

A service should have one clear responsibility.

Services must not contain HTTP concerns.

Services must not directly become generic utility libraries.

---

### Feature Modules

Feature-specific models, constants, exceptions, and helper modules belong here.

---

### ToolResult

Tool execution results must use the project's existing ToolResult contract.

Do not create competing result formats unnecessarily.

---

## 4. Feature Structure

Features generally follow:

feature/
├── models.py
├── constants.py
├── exceptions.py
├── service.py
└── tool.py

Additional submodules are allowed only when there is a demonstrated need.

Do not create abstractions merely because a design pattern exists.

---

## 5. Current Agent 1 Pipeline

Upload
↓
Storage
↓
Parser
↓
Classifier
↓
Extractor
↓
Validator
↓
Embedding Preparation
↓
Embedding Generation
↓
Vector Storage
↓
Retrieval
↓
AI Query

---

## 6. Deterministic / AI Boundary

The following stages are deterministic:

- Parser
- Classifier
- Extractor
- Validator
- Embedding Preparation

AI begins after deterministic processing.

AI-dependent stages include:

- Embedding Generation
- AI Query

Do not introduce AI into earlier deterministic stages unless the architecture is explicitly changed and the reason is reviewed first.

---

## 7. Document Independence

Documents are independent by default.

The system must never automatically:

- merge documents
- aggregate documents
- compare documents
- calculate combined totals
- create combined embeddings

Combination is allowed only when explicitly requested by the user.

---

## 8. Source of Truth

Original documents remain the canonical source.

Structured extraction is derived data.

Validation results are derived information.

Embeddings are derived representations.

ChromaDB is a retrieval index, not the canonical document store.

---

## 9. Immutability Principle

Processing stages should not silently modify the output of previous stages.

For example:

Validator:
Input → extracted document
Output → validation result

Validator must not repair or mutate the extracted document.

---

## 10. Architecture Evolution

Do not redesign the architecture without a demonstrated need.

When a component becomes genuinely difficult to maintain or a new requirement requires a structural change:

1. Identify the problem.
2. Explain why the current architecture is insufficient.
3. Propose the smallest appropriate change.
4. Review the change before implementation.
5. Preserve compatibility wherever possible.