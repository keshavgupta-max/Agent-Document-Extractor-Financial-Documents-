"""Focused unit and integration tests for VectorRetrievalService."""

from pathlib import Path
import pytest
from unittest.mock import MagicMock

from tests.test_vector_storage import _create_mock_embedding_payload
from tools.embedding.constants import DEFAULT_VECTOR_DIMENSIONS
from tools.vector_retrieval.constants import (
    DEFAULT_COLLECTION_NAME,
    MAX_TOP_K,
    META_KEY_CHUNK_ID,
    META_KEY_CHUNK_INDEX,
    META_KEY_DOCUMENT_ID,
    META_KEY_DOCUMENT_TYPE,
    META_KEY_WORKSPACE_ID,
)
from tools.vector_retrieval.exceptions import (
    InvalidRetrievalInputError,
    VectorRetrievalOperationError,
)
from tools.vector_retrieval.models import VectorRetrievalInput
from tools.vector_retrieval.service import VectorRetrievalService
from tools.vector_storage.models import VectorStorageInput
from tools.vector_storage.service import VectorStorageService


@pytest.fixture
def isolated_chroma_setup(tmp_path: Path):
    """Initializes isolated ChromaDB with both storage and retrieval services."""
    chroma_dir = tmp_path / "chroma_retrieval_test"
    chroma_dir.mkdir(parents=True, exist_ok=True)

    storage_svc = VectorStorageService()
    storage_svc._persist_dir = chroma_dir
    storage_svc._collection_name = DEFAULT_COLLECTION_NAME

    retrieval_svc = VectorRetrievalService(persist_dir=chroma_dir, collection_name=DEFAULT_COLLECTION_NAME)

    # Populate Workspace A: doc_A1 and doc_A2
    storage_svc.store_embeddings(
        VectorStorageInput(
            generated_embeddings=_create_mock_embedding_payload(
                workspace_id="ws_A",
                document_id="doc_A1",
                chunk_prefix="chk_A1",
            )
        )
    )
    storage_svc.store_embeddings(
        VectorStorageInput(
            generated_embeddings=_create_mock_embedding_payload(
                workspace_id="ws_A",
                document_id="doc_A2",
                chunk_prefix="chk_A2",
            )
        )
    )

    # Populate Workspace B: doc_B1
    storage_svc.store_embeddings(
        VectorStorageInput(
            generated_embeddings=_create_mock_embedding_payload(
                workspace_id="ws_B",
                document_id="doc_B1",
                chunk_prefix="chk_B1",
            )
        )
    )

    return retrieval_svc


def test_retrieval_same_workspace_selected_doc(isolated_chroma_setup):
    """Test 1: Retrieval returns only matching document chunks within requested workspace."""
    query_vector = [0.01] * DEFAULT_VECTOR_DIMENSIONS
    retrieval_input = VectorRetrievalInput(
        workspace_id="ws_A",
        selected_document_ids=["doc_A1"],
        query_embedding=query_vector,
        top_k=5,
    )

    result = isolated_chroma_setup.retrieve(retrieval_input)

    assert result.total_results == 2
    for chunk in result.retrieved_chunks:
        assert chunk.workspace_id == "ws_A"
        assert chunk.document_id == "doc_A1"


def test_retrieval_same_workspace_unselected_doc_excluded(isolated_chroma_setup):
    """Test 2: Unselected document in same workspace is not returned."""
    query_vector = [0.01] * DEFAULT_VECTOR_DIMENSIONS
    retrieval_input = VectorRetrievalInput(
        workspace_id="ws_A",
        selected_document_ids=["doc_A1"],
        query_embedding=query_vector,
        top_k=5,
    )

    result = isolated_chroma_setup.retrieve(retrieval_input)

    returned_doc_ids = {chunk.document_id for chunk in result.retrieved_chunks}
    assert "doc_A2" not in returned_doc_ids


def test_cross_workspace_isolation(isolated_chroma_setup):
    """Test 3: Querying across workspace boundaries returns zero results."""
    query_vector = [0.01] * DEFAULT_VECTOR_DIMENSIONS
    retrieval_input = VectorRetrievalInput(
        workspace_id="ws_A",
        selected_document_ids=["doc_B1"],
        query_embedding=query_vector,
        top_k=5,
    )

    result = isolated_chroma_setup.retrieve(retrieval_input)
    assert result.total_results == 0
    assert len(result.retrieved_chunks) == 0


def test_empty_document_scope_rejected(isolated_chroma_setup):
    """Test 4: Empty selected_document_ids list is rejected by service retrieval validation."""
    query_vector = [0.01] * DEFAULT_VECTOR_DIMENSIONS
    retrieval_input = VectorRetrievalInput(
        workspace_id="ws_A",
        selected_document_ids=[],
        query_embedding=query_vector,
        top_k=5,
    )

    with pytest.raises(InvalidRetrievalInputError):
        isolated_chroma_setup.retrieve(retrieval_input)


@pytest.mark.parametrize("invalid_top_k", [0, -1, MAX_TOP_K + 1])
def test_invalid_top_k_boundaries_rejected(isolated_chroma_setup, invalid_top_k):
    """Test 5: Validate top_k lower and upper bounds rejected by service retrieval validation."""
    query_vector = [0.01] * DEFAULT_VECTOR_DIMENSIONS
    retrieval_input = VectorRetrievalInput(
        workspace_id="ws_A",
        selected_document_ids=["doc_A1"],
        query_embedding=query_vector,
        top_k=invalid_top_k,
    )

    with pytest.raises(InvalidRetrievalInputError):
        isolated_chroma_setup.retrieve(retrieval_input)


def test_invalid_query_embedding_dimension(isolated_chroma_setup):
    """Test 6: Query embedding dimension mismatch is rejected by service retrieval validation."""
    query_vector = [0.01] * (DEFAULT_VECTOR_DIMENSIONS - 10)
    retrieval_input = VectorRetrievalInput(
        workspace_id="ws_A",
        selected_document_ids=["doc_A1"],
        query_embedding=query_vector,
        top_k=5,
    )

    with pytest.raises(InvalidRetrievalInputError):
        isolated_chroma_setup.retrieve(retrieval_input)


def test_defense_in_depth_workspace_metadata_mismatch(isolated_chroma_setup, monkeypatch):
    """Test 7: Post-retrieval verification raises error if ChromaDB returns foreign workspace record."""
    query_vector = [0.01] * DEFAULT_VECTOR_DIMENSIONS
    retrieval_input = VectorRetrievalInput(
        workspace_id="ws_A",
        selected_document_ids=["doc_A1"],
        query_embedding=query_vector,
        top_k=5,
    )

    mock_client = MagicMock()
    mock_collection = MagicMock()
    mock_collection.query.return_value = {
        "ids": [["rec_foreign"]],
        "documents": [["Foreign chunk text"]],
        "metadatas": [
            [
                {
                    META_KEY_CHUNK_ID: "chk_0",
                    META_KEY_DOCUMENT_ID: "doc_A1",
                    META_KEY_WORKSPACE_ID: "ws_MALICIOUS",
                    META_KEY_CHUNK_INDEX: 0,
                    META_KEY_DOCUMENT_TYPE: "INVOICE",
                }
            ]
        ],
        "distances": [[0.05]],
    }
    mock_client.get_collection.return_value = mock_collection
    monkeypatch.setattr(isolated_chroma_setup, "_get_client", lambda: mock_client)

    with pytest.raises(VectorRetrievalOperationError):
        isolated_chroma_setup.retrieve(retrieval_input)


def test_defense_in_depth_missing_required_metadata(isolated_chroma_setup, monkeypatch):
    """Test 8: Post-retrieval verification raises error if required metadata fields are missing."""
    query_vector = [0.01] * DEFAULT_VECTOR_DIMENSIONS
    retrieval_input = VectorRetrievalInput(
        workspace_id="ws_A",
        selected_document_ids=["doc_A1"],
        query_embedding=query_vector,
        top_k=5,
    )

    mock_client = MagicMock()
    mock_collection = MagicMock()
    mock_collection.query.return_value = {
        "ids": [["rec_missing_meta"]],
        "documents": [["Incomplete chunk text"]],
        "metadatas": [
            [
                {
                    META_KEY_CHUNK_ID: "chk_0",
                    META_KEY_DOCUMENT_ID: "doc_A1",
                    META_KEY_WORKSPACE_ID: "ws_A",
                    META_KEY_CHUNK_INDEX: 0,
                }
            ]
        ],
        "distances": [[0.05]],
    }
    mock_client.get_collection.return_value = mock_collection
    monkeypatch.setattr(isolated_chroma_setup, "_get_client", lambda: mock_client)

    with pytest.raises(VectorRetrievalOperationError):
        isolated_chroma_setup.retrieve(retrieval_input)