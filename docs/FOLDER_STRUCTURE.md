# Project Folder Structure

## Root

Project/

├── app/
├── api/
├── core/
├── tools/
├── storage/
├── database/
├── docs/
├── config.py
├── logger.py
├── exceptions.py
└── requirements.txt

---

## app/

Application entry point and application-level wiring.

Current main entry point:

app/main.py

---

## api/

HTTP API layer.

The API layer should contain request/response handling and routing.

Current known API:

api/upload.py

---

## core/

Core runtime and shared execution architecture.

Includes concepts such as:

- Runtime
- AgentState
- Tool framework
- Tool execution
- ToolResult

---

## tools/

Feature tools and their associated services/models.

Current Agent 1 features include:

- Upload
- Parser
- Classifier
- Extractor
- Validator

Future features will include:

- Embedding preparation
- Embedding generation
- Vector storage
- Retrieval
- Query

---

## storage/

Storage-related application components.

Storage implementation uses:

database/storage/

---

## database/

Persistent application data and local infrastructure.

Current structure includes:

database/
├── storage/
├── chroma/
└── temp/

---

## docs/

Permanent project documentation and architecture decisions.

---

## Configuration

config.py

Contains application configuration.

---

## Logging

logger.py

Contains application logging configuration.

---

## Exceptions

exceptions.py

Contains application-level exceptions.

Feature-specific exceptions should remain inside the relevant feature module where appropriate.