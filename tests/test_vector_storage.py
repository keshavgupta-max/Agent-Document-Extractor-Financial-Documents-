"""Focused unit and integration tests for VectorStorageService."""

from pathlib import Path
import pytest

from tools.embedding.constants import DEFAULT_VECTOR_DIMENSIONS
from tools.embedding.models import (
    EmbeddingGenerationMetadata,
    GeneratedDocumentEmbeddings,
    SingleGeneratedEmbedding,
)
from tools.vector_storage.constants import DEFAULT_COLLECTION_NAME, ID_SEPARATOR
from tools.vector_storage.exceptions import InvalidVectorDataError
from tools.vector_storage.models import VectorStorageInput
from tools.vector_storage.service import VectorStorageService


def _create_mock_embedding_payload(
    workspace_id: str = "ws_test_01",
    document_id: str = "doc_test_01",
    document_type: str = "INVOICE",
    num_chunks: int = 2,
    dim: int = DEFAULT_VECTOR_DIMENSIONS,
    chunk_prefix: str = "chk",
) -> GeneratedDocumentEmbeddings:
    """Helper to build deterministic embedding payloads using actual repository models."""
    embeddings = []
    for idx in range(num_chunks):
        vec = [float(idx + 1) / 100.0] * dim
        embeddings.append(
            SingleGeneratedEmbedding(
                chunk_id=f"{chunk_prefix}_{idx}",
                document_id=document_id,
                workspace_id=workspace_id,
                chunk_index=idx,
                text_content=f"Sample text content for chunk {idx}",
                vector=vec,
                dimensions=dim,
            )
        )

    metadata = EmbeddingGenerationMetadata(
        document_id=document_id,
        workspace_id=workspace_id,
        document_type=document_type,
        embedding_model="text-embedding-004",
        total_chunks_processed=len(embeddings),
        vector_dimensions=dim,
        processing_time_ms=10.0,
    )

    return GeneratedDocumentEmbeddings(
        document_id=document_id,
        workspace_id=workspace_id,
        document_type=document_type,
        embeddings=embeddings,
        metadata=metadata,
    )


@pytest.fixture
def temp_storage_service(tmp_path: Path):
    """Provides VectorStorageService connected to an isolated temporary Chroma directory."""
    chroma_dir = tmp_path / "chroma_storage_test"
    chroma_dir.mkdir(parents=True, exist_ok=True)

    service = VectorStorageService()
    service._persist_dir = chroma_dir
    service._collection_name = DEFAULT_COLLECTION_NAME
    return service


def test_successful_vector_persistence(temp_storage_service):
    """Test 1: Successful vector persistence to isolated ChromaDB."""
    payload = _create_mock_embedding_payload(num_chunks=2)
    storage_input = VectorStorageInput(generated_embeddings=payload)

    result = temp_storage_service.store_embeddings(storage_input)

    assert result.workspace_id == "ws_test_01"
    assert result.document_id == "doc_test_01"
    assert result.stored_count == 2
    assert result.collection_name == DEFAULT_COLLECTION_NAME
    assert len(result.record_ids) == 2


def test_metadata_preservation(temp_storage_service):
    """Test 2: Verify all required security and business metadata are accurately preserved in stored records."""
    payload = _create_mock_embedding_payload(num_chunks=1)
    storage_input = VectorStorageInput(generated_embeddings=payload)

    temp_storage_service.store_embeddings(storage_input)

    client = temp_storage_service._get_client()
    collection = client.get_collection(name=DEFAULT_COLLECTION_NAME)
    stored = collection.get(include=["metadatas", "documents"])

    assert len(stored["ids"]) == 1
    meta = stored["metadatas"][0]
    assert meta["workspace_id"] == "ws_test_01"
    assert meta["document_id"] == "doc_test_01"
    assert meta["chunk_id"] == "chk_0"
    assert meta["chunk_index"] == 0
    assert meta["document_type"] == "INVOICE"
    assert stored["documents"][0] == "Sample text content for chunk 0"


def test_deterministic_record_identity(temp_storage_service):
    """Test 3: Verify record ID formatting remains deterministic across executions."""
    payload = _create_mock_embedding_payload(num_chunks=1)
    storage_input = VectorStorageInput(generated_embeddings=payload)

    temp_storage_service.store_embeddings(storage_input)

    client = temp_storage_service._get_client()
    collection = client.get_collection(name=DEFAULT_COLLECTION_NAME)
    stored = collection.get()

    expected_record_id = f"ws_test_01{ID_SEPARATOR}doc_test_01{ID_SEPARATOR}chk_0"
    assert stored["ids"][0] == expected_record_id


def test_idempotent_re_ingestion(temp_storage_service):
    """Test 4: Store same vector records twice to verify idempotent upsert without duplicates."""
    payload = _create_mock_embedding_payload(num_chunks=2)
    storage_input = VectorStorageInput(generated_embeddings=payload)

    result_first = temp_storage_service.store_embeddings(storage_input)
    assert result_first.stored_count == 2

    result_second = temp_storage_service.store_embeddings(storage_input)
    assert result_second.stored_count == 2

    client = temp_storage_service._get_client()
    collection = client.get_collection(name=DEFAULT_COLLECTION_NAME)
    stored = collection.get()

    # Total unique entries in Chroma must remain 2
    assert len(stored["ids"]) == 2


def test_duplicate_chunk_id_validation(temp_storage_service):
    """Test 5: Verify input containing duplicate chunk IDs is rejected."""
    payload = _create_mock_embedding_payload(num_chunks=1)
    duplicate_chunk = SingleGeneratedEmbedding(
        chunk_id="chk_0",
        document_id="doc_test_01",
        workspace_id="ws_test_01",
        chunk_index=1,
        text_content="Duplicate chunk text",
        vector=[0.1] * DEFAULT_VECTOR_DIMENSIONS,
        dimensions=DEFAULT_VECTOR_DIMENSIONS,
    )
    payload.embeddings.append(duplicate_chunk)
    payload.metadata.total_chunks_processed = len(payload.embeddings)

    storage_input = VectorStorageInput(generated_embeddings=payload)

    with pytest.raises(InvalidVectorDataError):
        temp_storage_service.store_embeddings(storage_input)


def test_vector_dimension_validation(temp_storage_service):
    """Test 6: Verify payload with declared metadata dimension mismatch is rejected."""
    payload = _create_mock_embedding_payload(num_chunks=1, dim=DEFAULT_VECTOR_DIMENSIONS)
    payload.metadata.vector_dimensions = DEFAULT_VECTOR_DIMENSIONS + 10

    storage_input = VectorStorageInput(generated_embeddings=payload)

    with pytest.raises(InvalidVectorDataError):
        temp_storage_service.store_embeddings(storage_input)


def test_empty_embedding_input(temp_storage_service):
    """Test 7: Verify empty embedding payload is rejected."""
    payload = _create_mock_embedding_payload(num_chunks=0)
    storage_input = VectorStorageInput(generated_embeddings=payload)

    with pytest.raises(InvalidVectorDataError):
        temp_storage_service.store_embeddings(storage_input)