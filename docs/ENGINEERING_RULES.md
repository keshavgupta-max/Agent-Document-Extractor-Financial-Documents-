# Permanent Engineering Rules

These rules apply to the entire project.

They are permanent unless an explicit architectural decision changes them.

---

## 1. Do Not Redesign Existing Architecture

Do not introduce a new architecture when an existing project pattern already solves the problem.

Study existing modules before creating new patterns.

---

## 2. Single Responsibility

Every:

- class
- module
- service
- function

must have a clear responsibility.

Avoid God classes and God services.

---

## 3. Avoid Overengineering

Do not introduce unnecessary:

- factories
- repositories
- strategy patterns
- abstract base classes
- dependency injection frameworks
- managers
- registries
- layers

unless there is a real requirement.

Prefer the simplest solution that satisfies current and reasonably foreseeable requirements.

---

## 4. Scalability

When designing a component, ask:

"If the system grows significantly, will this component remain maintainable?"

Do not prematurely create abstractions for hypothetical problems.

Refactor when a real architectural need appears.

---

## 5. Existing Patterns

Follow established project patterns.

If Parser, Extractor, or another feature uses a particular organization, reuse that approach where appropriate.

Consistency is preferred over unnecessary novelty.

---

## 6. Business Rules

Do not scatter business rules throughout code.

Business constants, thresholds, patterns, and supported values should be centralized appropriately.

Avoid magic numbers and magic strings.

---

## 7. Enums

Use enums for important business categories and states.

Do not rely on fragile string comparisons when an established enum exists.

---

## 8. Utilities

Generic reusable operations belong in appropriate utility modules.

Do not turn feature services into collections of generic helper functions.

---

## 9. Layer Separation

API:
HTTP responsibilities.

Runtime:
execution orchestration.

Tool:
runtime-to-service integration.

Service:
business logic.

Models:
data structures.

Constants:
constants.

Exceptions:
feature-specific errors.

Utilities:
generic reusable functionality.

Do not mix responsibilities.

---

## 10. Strong Typing

Use:

- Python type hints
- Pydantic v2
- explicit models

Avoid unnecessary `Any`.

---

## 11. Immutability

Do not silently modify input models.

Prefer producing explicit outputs.

---

## 12. Security

Never trust:

- uploaded filenames
- user input
- document contents
- external data

Never expose:

- internal filesystem paths
- credentials
- API keys
- sensitive internal information

Never give an AI model arbitrary filesystem access.

---

## 13. Document Isolation

Always preserve:

- workspace identity
- document identity
- chunk identity

Never accidentally mix documents.

---

## 14. AI Boundary

Do not use AI when deterministic processing is sufficient.

Do not move AI into earlier pipeline stages merely for convenience.

---

## 15. Error Handling

Use meaningful feature-specific exceptions.

Do not expose internal implementation details through APIs.

Handle failures explicitly.

---

## 16. Maintainability

Before finalizing code ask:

- Can this be simpler?
- Does it follow existing architecture?
- Is responsibility clear?
- Is logic duplicated?
- Are there magic values?
- Will future engineers understand it?
- Does it create unnecessary coupling?

---

## 17. Backward Compatibility

Do not casually modify interfaces already used by completed phases.

If a change is genuinely necessary:

1. Explain the reason.
2. Identify affected components.
3. Propose the smallest change.
4. Review before implementation.

---

## 18. Code Generation Discipline

When implementing a requested phase:

- Follow the approved architecture.
- Implement only the requested scope.
- Do not silently implement future phases.
- Do not modify unrelated modules.
- Do not generate unnecessary files.

---

## 19. Self-Review

Before returning code, review it against these rules.

If a design violates an existing rule, fix it before returning the code.