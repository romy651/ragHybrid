import os
from pydantic import BaseModel, Field
from typing import Any, Literal, Optional

from langchain_core.runnables import RunnableConfig


class Configuration(BaseModel):
    """The configuration for the agent."""
    
    persona: Literal["product_owner", "marketing"] = Field(
        default="product_owner",
        metadata={
            "description": "The persona of the agent. Product owner: the agent is a product owner. Marketing: the agent is a marketing expert."
        },
    )
    
    reasoning_model: str = Field(
        default="gpt-3.5-turbo",
        metadata={
            "description": "The name of the language model to use for the agent's reasoning."
        },
    )
    

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig."""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )

        # Get raw values from environment or config
        raw_values: dict[str, Any] = {
            name: os.environ.get(name.upper(), configurable.get(name))
            for name in cls.model_fields.keys()
        }

        # Filter out None values
        values = {k: v for k, v in raw_values.items() if v is not None}

        return cls(**values)
