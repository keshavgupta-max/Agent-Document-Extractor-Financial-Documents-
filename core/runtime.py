"""Phase 15 Pipeline Execution Orchestrator.

Sequentially executes the Agent 1 document intelligence pipeline tools
using ToolRegistry and AgentState.
"""

import mimetypes
import time
from pathlib import Path
from typing import Any, Optional

from core.runtime_models import (
    ExecutionMode,
    IngestionPipelineInput,
    PipelineExecutionResult,
    PipelineStageExecution,
    QueryPipelineInput,
)
from core.state import AgentState
from core.tool_registry import ToolRegistry, ToolRegistryError
from logger import logger
from tools.classifier.models import ClassifierInput
from tools.embedding.models import EmbeddingInput
from tools.embedding_prep.models import EmbeddingPrepInput
from tools.extractor.models import ExtractorInput
from tools.parser.models import ParserInput
from tools.query.models import QueryInput
from tools.upload.constants import ALLOWED_MIME_TYPES
from tools.upload.models import UploadInput
from tools.validator.models import ValidationInput
from tools.vector_storage.models import VectorStorageInput

# Derive canonical extension-to-MIME mapping from project constants
EXTENSION_TO_CANONICAL_MIME = {
    ext: mime_type
    for mime_type, exts in ALLOWED_MIME_TYPES.items()
    for ext in exts
}

# Canonical staging root for incoming un-ingested source files
CANONICAL_STAGING_ROOT = Path("data/staging")


class AgentRuntime:
    """Core pipeline execution engine responsible for orchestrating tool dependency chains."""

    def __init__(
        self,
        registry: Optional[ToolRegistry] = None,
        staging_root: Optional[Path] = None,
    ) -> None:
        self._registry = registry or ToolRegistry()
        self._staging_root = Path(staging_root) if staging_root else CANONICAL_STAGING_ROOT

    async def execute_tool(
        self,
        tool_name: str,
        input_data: Any,
    ):
        """Execute a single registered tool through the runtime."""

        workspace_id = getattr(input_data, "workspace_id", None) or "api_request"
        state = AgentState(workspace_id=workspace_id)

        tool = self._registry.get(tool_name)

        if not tool:
            raise ToolRegistryError(
                f"Tool '{tool_name}' is not registered in ToolRegistry."
            )

        return await tool.run(
            state=state,
            input_data=input_data,
        )

    def _resolve_stage_tool_name(
        self,
        current_name: str,
        legacy_name: str,
    ) -> str:
        """Resolve current production tool name with legacy test compatibility."""

        if self._registry.get(current_name):
            return current_name

        if self._registry.get(legacy_name):
            return legacy_name

        return current_name

    async def run_ingestion_pipeline(
        self,
        payload: IngestionPipelineInput,
    ) -> PipelineExecutionResult:
        """Execute the full document ingestion pipeline sequentially."""

        start_time = time.perf_counter()
        workspace_id = payload.workspace_id.strip()

        if not workspace_id:
            return PipelineExecutionResult(
                success=False,
                mode=ExecutionMode.DOCUMENT_INGESTION,
                workspace_id="UNKNOWN",
                error_message="Mandatory field 'workspace_id' cannot be empty.",
            )

        state = AgentState(workspace_id=workspace_id)
        stages: list[PipelineStageExecution] = []
        document_id: Optional[str] = None

        logger.info(
            "Starting document ingestion pipeline for workspace: %s",
            workspace_id,
        )

        try:
            # ==============================================================
            # Stage 1: Upload Document
            # ==============================================================

            # Enforce strict path containment within the approved staging root
            allowed_staging_root = self._staging_root.resolve()

            input_path = Path(payload.file_path)
            resolved_input_path = input_path.resolve()

            try:
                is_inside_staging = resolved_input_path.is_relative_to(allowed_staging_root)
            except (ValueError, AttributeError):
                is_inside_staging = False

            if not is_inside_staging:
                logger.warning(
                    "Security violation: Requested source file_path '%s' is outside approved staging boundary '%s'.",
                    payload.file_path,
                    allowed_staging_root,
                )
                return self._build_failure_result(
                    ExecutionMode.DOCUMENT_INGESTION,
                    workspace_id,
                    stages,
                    start_time,
                    document_id,
                    "upload_document",
                )

            if not input_path.exists():
                return self._build_failure_result(
                    ExecutionMode.DOCUMENT_INGESTION,
                    workspace_id,
                    stages,
                    start_time,
                    document_id,
                    "upload_document",
                )

            if not input_path.is_file():
                return self._build_failure_result(
                    ExecutionMode.DOCUMENT_INGESTION,
                    workspace_id,
                    stages,
                    start_time,
                    document_id,
                    "upload_document",
                )

            file_bytes = input_path.read_bytes()

            file_extension = input_path.suffix.lower()
            mime_type = EXTENSION_TO_CANONICAL_MIME.get(file_extension) or mimetypes.guess_type(input_path.name)[0]
            mime_type = mime_type or "application/octet-stream"

            upload_input = UploadInput(
                filename=payload.original_filename,
                content=file_bytes,
                mime_type=mime_type,
                workspace_id=workspace_id,
                uploaded_by="system",
            )

            upload_res = await self._execute_stage(
                "upload_document",
                state,
                upload_input,
                stages,
            )

            if not upload_res.success or upload_res.data is None:
                return self._build_failure_result(
                    ExecutionMode.DOCUMENT_INGESTION,
                    workspace_id,
                    stages,
                    start_time,
                    document_id,
                    "upload_document",
                )

            data_dict = (
                upload_res.data
                if isinstance(upload_res.data, dict)
                else getattr(upload_res.data, "__dict__", {})
            )

            document_id = data_dict.get("document_id")

            # Canonical storage path is provided by UploadTool after persisting
            file_path = data_dict.get("storage_path")

            if not file_path:
                return self._build_failure_result(
                    ExecutionMode.DOCUMENT_INGESTION,
                    workspace_id,
                    stages,
                    start_time,
                    document_id,
                    "upload_document",
                )

            mime_type = data_dict.get("mime_type") or mime_type
            file_extension = (
                data_dict.get("file_extension")
                or Path(file_path).suffix.lower()
            )

            # ==============================================================
            # Stage 2: Parser
            # ==============================================================

            parser_input = ParserInput(
                document_id=document_id,
                storage_path=file_path,
                file_extension=file_extension,
                mime_type=mime_type,
            )

            parser_res = await self._execute_stage(
                "parse_document",
                state,
                parser_input,
                stages,
            )

            if not parser_res.success or parser_res.data is None:
                return self._build_failure_result(
                    ExecutionMode.DOCUMENT_INGESTION,
                    workspace_id,
                    stages,
                    start_time,
                    document_id,
                    "parse_document",
                )

            # ==============================================================
            # Stage 3: Classifier
            # ==============================================================

            classifier_input = ClassifierInput(
                parsed_document=parser_res.data,
            )

            classifier_res = await self._execute_stage(
                "classify_document",
                state,
                classifier_input,
                stages,
            )

            if not classifier_res.success or classifier_res.data is None:
                return self._build_failure_result(
                    ExecutionMode.DOCUMENT_INGESTION,
                    workspace_id,
                    stages,
                    start_time,
                    document_id,
                    "classify_document",
                )

            # ==============================================================
            # Stage 4: Extractor
            # ==============================================================

            classifier_data = (
                classifier_res.data
                if isinstance(classifier_res.data, dict)
                else getattr(classifier_res.data, "__dict__", {})
            )

            if isinstance(classifier_data, dict):
                doc_type = classifier_data.get("document_type")
            else:
                doc_type = getattr(
                    classifier_data,
                    "document_type",
                    None,
                )

            if not doc_type:
                return self._build_failure_result(
                    ExecutionMode.DOCUMENT_INGESTION,
                    workspace_id,
                    stages,
                    start_time,
                    document_id,
                    "classify_document",
                )

            extractor_input = ExtractorInput(
                parsed_document=parser_res.data,
                classification=classifier_res.data,
                document_type=doc_type,
            )

            extractor_res = await self._execute_stage(
                "extract_structured_data",
                state,
                extractor_input,
                stages,
            )

            if not extractor_res.success or extractor_res.data is None:
                return self._build_failure_result(
                    ExecutionMode.DOCUMENT_INGESTION,
                    workspace_id,
                    stages,
                    start_time,
                    document_id,
                    "extract_structured_data",
                )

            # ==============================================================
            # Stage 5: Validator
            # ==============================================================

            validator_input = ValidationInput(
                structured_document=extractor_res.data,
            )

            validator_res = await self._execute_stage(
                "validate_document",
                state,
                validator_input,
                stages,
            )

            if not validator_res.success or validator_res.data is None:
                return self._build_failure_result(
                    ExecutionMode.DOCUMENT_INGESTION,
                    workspace_id,
                    stages,
                    start_time,
                    document_id,
                    "validate_document",
                )

            val_data = (
                validator_res.data
                if isinstance(validator_res.data, dict)
                else getattr(validator_res.data, "__dict__", {})
            )

            if isinstance(val_data, dict):
                is_valid = val_data.get("is_valid")

                if is_valid is None:
                    validation_status = str(
                        val_data.get("status", "")
                    ).upper()

                    is_valid = validation_status in {
                        "PASSED",
                        "PASSED_WITH_WARNINGS",
                    }
            else:
                is_valid = getattr(
                    val_data,
                    "is_valid",
                    None,
                )

                if is_valid is None:
                    validation_status = str(
                        getattr(val_data, "status", "")
                    ).upper()

                    is_valid = validation_status in {
                        "PASSED",
                        "PASSED_WITH_WARNINGS",
                    }

            if not is_valid:
                logger.warning(
                    "Validation failed for doc_id '%s'. "
                    "Stopping pipeline before embedding prep.",
                    document_id,
                )

                return PipelineExecutionResult(
                    success=False,
                    mode=ExecutionMode.DOCUMENT_INGESTION,
                    workspace_id=workspace_id,
                    document_id=document_id,
                    failed_stage="validate_document",
                    stages=stages,
                    total_execution_time_ms=round(
                        (time.perf_counter() - start_time) * 1000.0,
                        2,
                    ),
                    error_message=(
                        "Document validation failed due to "
                        "business constraint violations."
                    ),
                )

            # ==============================================================
            # Stage 6: Embedding Preparation
            # ==============================================================

            prep_input = EmbeddingPrepInput(
                workspace_id=workspace_id,
                structured_document=extractor_res.data,
                parsed_document=parser_res.data,
                is_valid=is_valid,
            )

            prep_res = await self._execute_stage(
                "prepare_embedding_content",
                state,
                prep_input,
                stages,
            )

            if not prep_res.success or prep_res.data is None:
                return self._build_failure_result(
                    ExecutionMode.DOCUMENT_INGESTION,
                    workspace_id,
                    stages,
                    start_time,
                    document_id,
                    "prepare_embedding_content",
                )

            # ==============================================================
            # Stage 7: Embedding Generation
            # ==============================================================

            embedding_input = EmbeddingInput(
                prepared_content=prep_res.data,
            )

            embedding_res = await self._execute_stage(
                "generate_embeddings",
                state,
                embedding_input,
                stages,
            )

            if not embedding_res.success or embedding_res.data is None:
                return self._build_failure_result(
                    ExecutionMode.DOCUMENT_INGESTION,
                    workspace_id,
                    stages,
                    start_time,
                    document_id,
                    "generate_embeddings",
                )

            # ==============================================================
            # Stage 8: Vector Storage
            # ==============================================================

            storage_input = VectorStorageInput(
                generated_embeddings=embedding_res.data,
            )

            storage_res = await self._execute_stage(
                "store_vectors",
                state,
                storage_input,
                stages,
            )

            if not storage_res.success or storage_res.data is None:
                return self._build_failure_result(
                    ExecutionMode.DOCUMENT_INGESTION,
                    workspace_id,
                    stages,
                    start_time,
                    document_id,
                    "store_vectors",
                )

            # ==============================================================
            # Successful Pipeline
            # ==============================================================

            elapsed_ms = (
                time.perf_counter() - start_time
            ) * 1000.0

            logger.info(
                "Successfully ingested document '%s' in %.2fms",
                document_id,
                elapsed_ms,
            )

            return PipelineExecutionResult(
                success=True,
                mode=ExecutionMode.DOCUMENT_INGESTION,
                workspace_id=workspace_id,
                document_id=document_id,
                final_output=storage_res.data,
                stages=stages,
                total_execution_time_ms=round(
                    elapsed_ms,
                    2,
                ),
            )

        except Exception as exc:
            logger.error(
                "Unhandled runtime exception during ingestion: %s",
                str(exc),
                exc_info=True,
            )

            failed_stage_name = (
                stages[-1].tool_name
                if stages
                else None
            )

            elapsed_ms = (
                time.perf_counter() - start_time
            ) * 1000.0

            return PipelineExecutionResult(
                success=False,
                mode=ExecutionMode.DOCUMENT_INGESTION,
                workspace_id=workspace_id,
                document_id=document_id,
                failed_stage=failed_stage_name,
                stages=stages,
                total_execution_time_ms=round(
                    elapsed_ms,
                    2,
                ),
                error_message=(
                    "An internal error occurred while "
                    "executing the document ingestion pipeline."
                ),
            )

    async def run_query_pipeline(
        self,
        payload: QueryPipelineInput,
    ) -> PipelineExecutionResult:
        """Execute grounded query pipeline by invoking QueryTool directly."""

        start_time = time.perf_counter()
        workspace_id = payload.workspace_id.strip()

        if not workspace_id:
            return PipelineExecutionResult(
                success=False,
                mode=ExecutionMode.QUERY,
                workspace_id="UNKNOWN",
                error_message="Mandatory field 'workspace_id' cannot be empty.",
            )

        state = AgentState(workspace_id=workspace_id)
        stages: list[PipelineStageExecution] = []

        try:
            query_input = QueryInput(
                workspace_id=workspace_id,
                selected_document_ids=payload.selected_document_ids,
                query=payload.query,
                top_k=payload.top_k,
            )

            query_res = await self._execute_stage(
                "query_documents",
                state,
                query_input,
                stages,
            )

            elapsed_ms = (
                time.perf_counter() - start_time
            ) * 1000.0

            if not query_res.success or query_res.data is None:
                return PipelineExecutionResult(
                    success=False,
                    mode=ExecutionMode.QUERY,
                    workspace_id=workspace_id,
                    failed_stage="query_documents",
                    stages=stages,
                    total_execution_time_ms=round(
                        elapsed_ms,
                        2,
                    ),
                    error_message=(
                        query_res.error
                        or "Query processing failed."
                    ),
                )

            return PipelineExecutionResult(
                success=True,
                mode=ExecutionMode.QUERY,
                workspace_id=workspace_id,
                final_output=query_res.data,
                stages=stages,
                total_execution_time_ms=round(
                    elapsed_ms,
                    2,
                ),
            )

        except Exception as exc:
            logger.error(
                "Unhandled runtime exception during query: %s",
                str(exc),
                exc_info=True,
            )

            elapsed_ms = (
                time.perf_counter() - start_time
            ) * 1000.0

            return PipelineExecutionResult(
                success=False,
                mode=ExecutionMode.QUERY,
                workspace_id=workspace_id,
                failed_stage="query_documents",
                stages=stages,
                total_execution_time_ms=round(
                    elapsed_ms,
                    2,
                ),
                error_message=(
                    "An internal error occurred while "
                    "executing the document query."
                ),
            )

    async def _execute_stage(
        self,
        tool_name: str,
        state: AgentState,
        input_data: Any,
        stages_log: list[PipelineStageExecution],
    ):
        """Look up a tool, execute it, and record its execution result."""

        tool = self._registry.get(tool_name)

        if not tool:
            error_msg = (
                f"Tool '{tool_name}' is not registered in ToolRegistry."
            )

            logger.error(error_msg)

            stages_log.append(
                PipelineStageExecution(
                    tool_name=tool_name,
                    success=False,
                    error=error_msg,
                )
            )

            raise ToolRegistryError(error_msg)

        res = await tool.run(
            state=state,
            input_data=input_data,
        )

        stages_log.append(
            PipelineStageExecution(
                tool_name=tool_name,
                success=res.success,
                execution_time_ms=res.execution_time_ms,
                error=res.error if not res.success else None,
            )
        )

        return res

    def _build_failure_result(
        self,
        mode: ExecutionMode,
        workspace_id: str,
        stages: list[PipelineStageExecution],
        start_time: float,
        document_id: Optional[str],
        failed_stage: str,
    ) -> PipelineExecutionResult:
        """Construct sanitized failure output when a stage stops execution."""

        last_error = (
            stages[-1].error
            if stages and stages[-1].error
            else "Stage execution failed."
        )

        elapsed_ms = (
            time.perf_counter() - start_time
        ) * 1000.0

        logger.warning(
            "Pipeline halted at stage '%s' for workspace '%s'. Error: %s",
            failed_stage,
            workspace_id,
            last_error,
        )

        return PipelineExecutionResult(
            success=False,
            mode=mode,
            workspace_id=workspace_id,
            document_id=document_id,
            failed_stage=failed_stage,
            stages=stages,
            total_execution_time_ms=round(
                elapsed_ms,
                2,
            ),
            error_message=(
                f"Pipeline stopped at stage '{failed_stage}': "
                f"{last_error}"
            ),
        )