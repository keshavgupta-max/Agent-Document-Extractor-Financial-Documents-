"""Central registry for discovering and managing available agent tools."""

from typing import Any, Dict, List, Optional

from core.base_tool import BaseTool
from exceptions import BaseAgentException
from logger import logger
from tools.classifier.tool import ClassifierTool
from tools.embedding.tool import EmbeddingTool
from tools.embedding_prep.tool import EmbeddingPrepTool
from tools.extractor.tool import ExtractorTool
from tools.parser.tool import ParserTool
from tools.query.tool import QueryTool
from tools.upload.tool import UploadTool
from tools.validator.tool import ValidationTool
from tools.vector_retrieval.tool import VectorRetrievalTool
from tools.vector_storage.tool import VectorStorageTool


class ToolRegistryError(BaseAgentException):
    """Raised when tool registration or lookup operations fail."""

    pass


class ToolRegistry:
    """Registry holding instantiated tool instances."""

    def __init__(self) -> None:
        self._tools: Dict[str, BaseTool] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """Helper method to register core pipeline tools upon initialization.

        Raises:
            ToolRegistryError: If any default tool fails to initialize or register.
        """
        try:
            upload_tool = UploadTool()
            self.register(upload_tool)

            parser_tool = ParserTool()
            self.register(parser_tool)

            classifier_tool = ClassifierTool()
            self.register(classifier_tool)

            extractor_tool = ExtractorTool()
            self.register(extractor_tool)

            validation_tool = ValidationTool()
            self.register(validation_tool)

            embedding_prep_tool = EmbeddingPrepTool()
            self.register(embedding_prep_tool)

            embedding_tool = EmbeddingTool()
            self.register(embedding_tool)

            vector_storage_tool = VectorStorageTool()
            self.register(vector_storage_tool)

            vector_retrieval_tool = VectorRetrievalTool()
            self.register(vector_retrieval_tool)

            query_tool = QueryTool()
            self.register(query_tool)

            logger.info("Default tools registered successfully in ToolRegistry.")
        except Exception as exc:
            error_msg = f"Failed to register default pipeline tools: {str(exc)}"
            logger.error(error_msg, exc_info=True)
            raise ToolRegistryError(error_msg) from exc

    def register(self, tool: BaseTool) -> None:
        """Registers a tool instance. Prevents duplicate tool registration.

        Raises:
            ToolRegistryError: If a tool with the same name is already registered.
        """
        if not isinstance(tool, BaseTool):
            error_msg = f"Invalid tool type. Must inherit from BaseTool: {type(tool)}"
            logger.error(error_msg)
            raise ToolRegistryError(error_msg)

        if tool.name in self._tools:
            error_msg = f"Tool with name '{tool.name}' is already registered."
            logger.error(error_msg)
            raise ToolRegistryError(error_msg)

        self._tools[tool.name] = tool
        logger.info("Successfully registered tool: %s", tool.name)

    def get(self, name: str) -> Optional[BaseTool]:
        """Retrieves a registered tool by name."""
        return self._tools.get(name)

    def is_registered(self, name: str) -> bool:
        """Checks if a tool is registered."""
        return name in self._tools

    def list_tools(self) -> List[str]:
        """Returns a list of all registered tool names."""
        return list(self._tools.keys())

    def get_schemas(self) -> List[Dict[str, Any]]:
        """Returns structured JSON schemas of all registered tools for LLM binding."""
        schemas = []
        for tool in self._tools.values():
            schemas.append(
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_model.model_json_schema(),
                }
            )
        return schemas