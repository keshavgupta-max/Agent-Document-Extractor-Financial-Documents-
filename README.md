# 🤖 Agent 1 — Business Document Intelligence

<div align="center">

## AI-Powered Document Processing • Validation • Retrieval • RAG

**Transform business and financial documents into structured, validated, searchable intelligence.**

<br>

![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Gemini](https://img.shields.io/badge/Google-Gemini-4285F4?style=for-the-badge&logo=google)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_DB-FF6B35?style=for-the-badge)
![Pytest](https://img.shields.io/badge/Tests-pytest-0A9EDC?style=for-the-badge&logo=pytest)

</div>

---

## 📌 Overview

**Agent 1** is a Business Document Intelligence backend designed to process business and financial documents through a **deterministic-first architecture**.

It combines structured document processing with embeddings, vector retrieval, and grounded Gemini-based question answering.

### 🔄 End-to-End Workflow

<div align="center">

| 📄 **DOCUMENT** | ⬆️ **UPLOAD** | 📖 **PARSE** | 🏷️ **CLASSIFY** |
|:---:|:---:|:---:|:---:|
| Input | Ingestion | Structure | Document Type |

⬇️

| 🔍 **EXTRACT** | ✅ **VALIDATE** | 🧩 **EMBEDDING PREP** | 🧠 **EMBEDDING** |
|:---:|:---:|:---:|:---:|
| Business Data | Business Rules | Semantic Content | Vector |

⬇️

| 🗄️ **CHROMADB** | 🔎 **RETRIEVAL** | 🤖 **GEMINI RAG** |
|:---:|:---:|:---:|
| Vector Index | Relevant Context | Grounded Answer |

</div>

> **Core principle:** deterministic processing first, AI where semantic understanding and generation provide clear value.

---

## ✨ Key Features

<div align="center">

| | Capability | Description |
|:---:|:---|:---|
| 📄 | **Multi-format Processing** | PDF, DOCX, XLSX, CSV, TXT and images |
| 🧠 | **Classification** | Deterministic document type classification |
| 📊 | **Structured Extraction** | Business and financial field extraction |
| 🧾 | **Invoice Intelligence** | Subtotal, CGST, SGST, IGST, tax and grand total |
| ✅ | **Validation** | Business and financial consistency checks |
| 🔢 | **Embeddings** | Semantic representation of validated content |
| 🗄️ | **Vector Storage** | ChromaDB-based vector indexing |
| 🔎 | **Retrieval** | Workspace and document-scoped retrieval |
| 🤖 | **RAG Querying** | Gemini-powered document-grounded answers |
| 🔐 | **Isolation** | Workspace and selected-document boundaries |
| 📈 | **Observability** | Stage-level execution and latency measurement |
| 🧪 | **Testing** | Unit, API, integration and E2E testing |

</div>

---

## 🏗️ Architecture

Agent 1 uses a layered backend architecture that separates API handling, orchestration, tool execution, business logic and domain models.

### 🧱 Backend Architecture

<div align="center">

| 🟦 Layer | Responsibility |
|:---:|:---|
| 🌐 **API** | HTTP endpoints and request handling |
| ⚙️ **Runtime** | Pipeline orchestration and execution |
| 🔧 **Tool Executor** | Controlled tool execution |
| 🧩 **Tools** | Runtime-to-service integration |
| 🛠️ **Services** | Feature and business logic |
| 📦 **Domain Models** | Typed application data |

</div>

### 🔄 Processing Pipeline

<div align="center">

| Stage | Stage | Stage | Stage |
|:---:|:---:|:---:|:---:|
| 🟦 **UPLOAD** | 🟦 **PARSE** | 🟦 **CLASSIFY** | 🟦 **EXTRACT** |
| Document Input | Structure | Document Type | Business Data |

⬇️

| Stage | Stage | Stage | Stage |
|:---:|:---:|:---:|:---:|
| 🟩 **VALIDATE** | 🟨 **EMBED PREP** | 🟨 **EMBEDDING** | 🟪 **CHROMADB** |
| Business Rules | Semantic Content | Vector | Vector Index |

⬇️

| Stage | Stage | Stage |
|:---:|:---:|:---:|
| 🟪 **RETRIEVAL** | 🟥 **GEMINI RAG** | 🎯 **ANSWER** |
| Relevant Context | Grounded Generation | Sources + Response |

</div>

### 🧠 Deterministic → AI Boundary

<div align="center">

| 🟩 **DETERMINISTIC** | 🟪 **SEMANTIC / AI** |
|:---:|:---:|
| 📖 Parser | 🧠 Embeddings |
| 🏷️ Classifier | 🔎 Vector Retrieval |
| 🔍 Extractor | 🤖 Gemini Generation |
| ✅ Validator | |
| 🧩 Embedding Preparation | |

</div>

> Business-critical processing remains deterministic wherever practical. AI is introduced after validated processing for semantic representation and grounded querying.

---

## 🧾 Invoice Intelligence

The invoice extractor currently supports:

- Invoice number
- Invoice date
- Due date
- Seller and buyer information
- Line items
- Subtotal
- CGST
- SGST
- IGST
- Total tax
- Grand total

### Financial Extraction Example

<div align="center">

| Field | Value |
|:---|---:|
| **Subtotal** | `102000.00` |
| **CGST** | `9180.00` |
| **SGST** | `9180.00` |
| **Total Tax** | `18360.00` |
| **Grand Total** | `120360.00` |

</div>

Tax values are calculated dynamically from the document content and are **not hardcoded into production extraction logic**.

### Regression Fix

A substring collision was identified where `TOTAL` could incorrectly match `SUBTOTAL`.

The extractor now uses boundary-aware matching so that:

- `SUBTOTAL: 102000.00`
- `TOTAL: 120360.00`

are extracted as separate fields.

---

## 🔐 Security

<div align="center">

| 🔒 Security Area | Protection |
|:---|:---|
| Workspace Isolation | Documents remain scoped to their workspace |
| Document Isolation | Retrieval respects selected document boundaries |
| File Storage | Controlled storage paths |
| Input Security | Uploaded filenames treated as untrusted input |
| AI Security | No arbitrary filesystem access for AI |
| Credentials | API keys stored through environment variables |
| Retrieval Security | Workspace/document context enforced by backend |

</div>

---

## 🔎 RAG Query Flow

<div align="center">

**👤 User Question**

⬇️

**🧠 Query Embedding**

⬇️

**🔎 Filtered Retrieval**

⬇️

**📚 Context Construction**

⬇️

**🤖 Gemini Generation**

⬇️

**🎯 Grounded Answer + Sources**

</div>

---

## 📈 Query Performance

The query service measures latency across individual stages:

<div align="center">

| Stage | Measured |
|:---|:---:|
| Query Embedding | ✅ |
| Retrieval | ✅ |
| Context Construction | ✅ |
| AI Generation | ✅ |
| Total Query Time | ✅ |

</div>

This allows performance decisions to be based on measured bottlenecks rather than assumptions.

---

## 🧪 Testing

Run the complete test suite:

    .\.venv\Scripts\python.exe -m pytest

Run the invoice regression test:

    .\.venv\Scripts\python.exe -m pytest tests/test_invoice_extractor.py -v

### Current Verified Results

<div align="center">

| Test | Result |
|:---|:---:|
| InvoiceExtractor Regression | ✅ **1 passed** |
| Full Test Suite | ✅ **17 passed** |

</div>

The invoice workflow has also been verified through the complete processing path:

**PDF → Upload → Parse → Classify → Extract → Validate → Embedding → ChromaDB → Retrieval → Gemini Query**

---

## ⚙️ Technology Stack

<div align="center">

| Technology | Purpose |
|:---|:---|
| 🐍 **Python** | Backend |
| ⚡ **FastAPI** | REST API |
| 🛡️ **Pydantic v2** | Data validation |
| ✨ **Google Gemini** | AI generation |
| 🧠 **Embeddings** | Semantic representation |
| 🗄️ **ChromaDB** | Vector retrieval |
| 🧪 **pytest** | Testing |

</div>

---

## 📁 Project Structure

    Agent 1 Document to extract/
    ├── api/
    ├── app/
    ├── core/
    ├── data/
    ├── database/
    ├── docs/
    ├── models/
    ├── prompts/
    ├── storage/
    ├── tests/
    ├── tools/
    ├── utils/
    ├── config.py
    ├── exceptions.py
    ├── logger.py
    ├── requirements.txt
    ├── .gitignore
    └── README.md

---

## 🚀 Setup

### 1. Create Virtual Environment

    python -m venv .venv

### 2. Install Dependencies

    .\.venv\Scripts\python.exe -m pip install -r requirements.txt

### 3. Configure Environment

Create a `.env` file:

    GOOGLE_API_KEY=your_api_key_here

> ⚠️ Never commit `.env` or API keys to Git.

### 4. Run Tests

    .\.venv\Scripts\python.exe -m pytest

### 5. Run the API

    .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload

---

## 📐 Engineering Principles

- **Deterministic processing before AI**
- **Single responsibility**
- **Strong typing**
- **Explicit validation**
- **Document independence**
- **Backend-enforced security**
- **Regression-driven development**
- **Measure before optimizing**
- **Avoid premature abstraction**
- **Minimal production changes**

### Development Workflow

<div align="center">

**TEST** → **MEASURE** → **ANALYZE** → **DECIDE** → **CHANGE** → **RE-TEST**

</div>

Production architecture is not redesigned merely for theoretical improvements.

---

## 📌 Current Status

### ✅ Implemented

- [x] Document upload
- [x] Multi-format parsing
- [x] Document classification
- [x] Structured extraction
- [x] Financial validation
- [x] Embedding preparation
- [x] Embedding generation
- [x] ChromaDB vector storage
- [x] Document-scoped retrieval
- [x] Gemini RAG querying
- [x] Invoice regression testing
- [x] Query performance instrumentation
- [x] API, runtime and E2E testing

### 🔄 Current Focus

- [ ] Expand extractor regression coverage
- [ ] Edge-case testing
- [ ] Retrieval evaluation
- [ ] Security hardening
- [ ] Performance and scalability testing
- [ ] Production hardening

---

## 🔭 Roadmap

- Expand document and invoice coverage
- Improve retrieval evaluation
- Strengthen security testing
- Benchmark larger workloads
- Improve observability
- Production deployment hardening

---

## 👨‍💻 Author

<div align="center">

### **Keshav Gupta**

**B.Tech — Electronics & Communication Engineering**

AI/ML • LLM Applications • RAG • AI Agents • Backend Engineering • Document Intelligence

</div>

---

<div align="center">

### ⭐ Built with Python • FastAPI • Gemini • ChromaDB • pytest

</div>