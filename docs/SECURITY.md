# Security Architecture

## 1. Security Objective

The platform processes private business documents.

Security is a core architectural requirement.

---

## 2. Workspace Isolation

Documents must be isolated by workspace.

A user must only access documents belonging to authorized workspace(s).

---

## 3. Document Isolation

Every document must have a stable internal identity.

Documents must not be identified solely by their original filename.

---

## 4. Filename Security

Never trust uploaded filenames.

Do not use user-provided filenames directly as filesystem paths.

Use safe generated identifiers and controlled storage paths.

---

## 5. Filesystem Security

Users and AI components must never receive arbitrary filesystem access.

Internal filesystem paths must never be exposed through API responses.

---

## 6. AI Security

AI models must not have direct filesystem access.

AI should receive only the context explicitly prepared for the query.

---

## 7. Vector Security

Vector retrieval must preserve workspace and document boundaries.

Metadata filters must prevent cross-workspace retrieval.

---

## 8. Selected Document Rule

When a user selects specific documents for a query, retrieval must be restricted to those documents.

Example:

Selected:

Invoice A
Invoice C

Allowed retrieval:

Invoice A
Invoice C

Not allowed:

Invoice B
Invoice D
Other workspace documents

---

## 9. Document Combination

Documents must never be combined automatically.

Combination must be an explicit user operation.

---

## 10. Sensitive Data

Do not unnecessarily log or expose:

- document contents
- credentials
- API keys
- passwords
- internal paths
- sensitive personal/business information

---

## 11. Input Validation

Validate all externally supplied:

- file metadata
- identifiers
- query parameters
- document selections
- user queries

---

## 12. Security Principle

Security must be enforced by the backend architecture.

Security must never depend on the AI model following instructions.