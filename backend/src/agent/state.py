from __future__ import annotations
from typing import Literal, TypedDict
from langgraph.graph import add_messages
from typing_extensions import Annotated

class OverallState(TypedDict):
    messages: Annotated[list, add_messages]
    persona: Literal["product_owner", "marketing"]
    reasoning_model: Literal["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
    tool: Literal["rag", "analytic"]

