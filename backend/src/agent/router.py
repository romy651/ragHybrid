from typing import Literal
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, ConfigDict
from langchain_core.prompts import ChatPromptTemplate


class RouteQuery(BaseModel):
    """Route Query to determine the next step in the execution flow."""
    model_config = ConfigDict(extra="forbid")
    
    datasource: Literal["analytic", "rag"] = Field(
        ..., 
        description="Given the user query, choose the route to take to answer the query, analytics is used for sql aggregation over the sqlite database, rag is used for vector search over the documents")
    
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

structured_llm = llm.with_structured_output(RouteQuery)

system_prompt = """
You are an expert at routing a user question to either a vector store or a sqlite database.

Analytic is used for sql aggregation over the provided sqlite database (like sum, count, avg, etc.)

Rag is used to retrieve the most relevant documents from the provided vector store.

You will be given a user query and you will need to determine the best datasource to use to answer the query.

The datasource to use will depend on the user query.

If the user query is a question about the data in the sqlite database, you should return "analytic".

If the user query is a question about the documents in the vector store, you should return "rag".

You will need to return the datasource to use in the following format:

"""

route_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{query}")
    ]
)

question_router = route_prompt | structured_llm