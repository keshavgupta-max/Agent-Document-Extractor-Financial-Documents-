# Agent 1 Processing Pipeline

## 1. Overview

A business document follows this pipeline:

Upload
↓
Storage
↓
Parsing
↓
Classification
↓
Structured Extraction
↓
Validation
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

## 2. Upload

Input:

User-uploaded file.

Responsibilities:

- Validate upload request
- Establish document/workspace context
- Securely store the file
- Never trust the original filename

Output:

Stored document reference.

---

## 3. Storage

Stores original uploaded documents under controlled storage.

Storage must:

- Preserve workspace isolation
- Avoid arbitrary filesystem access
- Avoid exposing internal paths
- Use safe generated identifiers

---

## 4. Parsing

Supported formats:

- PDF
- DOCX
- XLSX
- CSV
- TXT
- Images

Parsing extracts information from the document.

Parsing does not:

- classify the document
- use AI
- perform OCR
- validate business rules
- generate embeddings

Output:

ParsedDocument.

---

## 5. Classification

Classification is deterministic.

It determines the business document type using established rules.

It does not use:

- AI
- ML
- OCR

Output:

DocumentClassification.

---

## 6. Structured Extraction

Extraction receives:

- ParsedDocument
- DocumentClassification

It produces structured business data.

Extraction does not:

- validate data
- calculate business KPIs
- use AI
- generate embeddings

Output:

StructuredBusinessDocument.

---

## 7. Validation

Validation receives structured extracted data.

It checks:

- required fields
- consistency
- dates
- currencies
- financial totals
- applicable business rules
- other deterministic validation conditions

Validation must not modify extracted data.

Output:

ValidationResult.

---

## 8. Embedding Preparation

Embedding preparation converts validated structured information into clean semantic content.

It prepares:

- embedding content
- chunks
- metadata
- document identity
- chunk identity

It does not:

- call an embedding API
- generate vectors
- access ChromaDB
- perform retrieval
- call an LLM

Output:

Embedding preparation result.

---

## 9. Embedding Generation

Embedding generation receives prepared chunks.

It calls the selected embedding provider.

Output:

Vectors associated with document/chunk identifiers.

---

## 10. Vector Storage

Vector storage stores:

- vectors
- chunk content
- metadata
- document identifiers

ChromaDB is an index for retrieval.

It is not the canonical document store.

---

## 11. Retrieval

Retrieval searches vector storage.

Retrieval MUST respect:

- workspace identity
- document identity
- user-selected documents

If the user selects Invoice A and Invoice C, retrieval must not return Invoice B.

---

## 12. AI Query

The AI receives:

- user question
- retrieved context
- relevant metadata

The AI should answer using retrieved document context.

The AI must not have arbitrary filesystem access.

The AI must not independently access documents outside the permitted retrieval scope.

---

## 13. Document Independence Rule

Documents remain independent unless the user explicitly requests a multi-document operation.

No stage may silently combine documents.