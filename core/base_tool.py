"""Abstract Base Class interface for all Agent tools."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Type, Union
from pydantic import BaseModel, Field

from core.state import AgentState
from core.tool_result import ToolResult


class BaseTool(ABC, BaseModel):
    """Abstract base class for all agent tools.

    Every concrete tool must define:
    - name: str
    - description: str
    - input_model: Type[BaseModel]
    - _run(): Coroutine returning ToolResult
    """

    name: str = Field(..., description="Unique name of the tool")
    description: str = Field(..., description="Description of tool capabilities")
    input_model: Type[BaseModel] = Field(
        ..., description="Pydantic model class used to validate tool input."
    )

    @abstractmethod
    async def _run(self, state: AgentState, input_data: BaseModel) -> ToolResult:
        """Execute the tool's core business logic.

        Must be implemented by every concrete tool subclass.

        Parameters
        ----------
        state : AgentState
            The active request execution state.
        input_data : BaseModel
            Validated instance of the tool's specific input_model.

        Returns
        -------
        ToolResult
            Result produced by the concrete tool.
        """
        raise NotImplementedError(
            "Concrete tool classes must implement the '_run' method."
        )

    async def run(
        self, state: AgentState, input_data: Union[BaseModel, Dict[str, Any]]
    ) -> ToolResult:
        """Validate input parameters against input_model and execute tool logic.

        Parameters
        ----------
        state : AgentState
            The active request execution state.
        args : Union[BaseModel, Dict[str, Any]]
            Tool input payload as a validated Pydantic model instance or raw dictionary.

        Returns
        -------
        ToolResult
            Standardized execution result object.
        """
        if isinstance(input_data, self.input_model):
            validated_input = input_data
        elif isinstance(input_data, dict):
            validated_input = self.input_model.model_validate(input_data)
        elif isinstance(input_data, BaseModel):
            validated_input = self.input_model.model_validate(input_data.model_dump())
        else:
            raise ValueError(
                f"Invalid input type '{type(input_data).__name__}' provided for tool '{self.name}'. "
                f"Expected instance of '{self.input_model.__name__}' or dict."
            )

        return await self._run(state=state, input_data=validated_input)