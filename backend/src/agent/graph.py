import logging
import json
from dotenv import load_dotenv
from langchain_core.messages import AIMessage
from langgraph.types import Send
from langgraph.graph import StateGraph
from langgraph.graph import END
from langchain_core.runnables import RunnableConfig

from agent.state import (
    OverallState
)
from agent.configuration import Configuration
from agent.router import RouteQuery, question_router
from wrangler.queryTranslation import translate_query
from wrangler.ragUtil import RAGUtils
from wrangler.qa_agent import OpenAIQuestionAnswerAgent

load_dotenv()



ROUTER_NODE = "router"
ANALYTIC_NODE = "analytic"
RAG_NODE = "rag"
FORMAT_NODE = "format"


def route_query(state: OverallState, config: RunnableConfig) -> OverallState:
    """LangGraph node that routes the query to the appropriate datasource."""
    question = state["messages"][0].content
    datasource: RouteQuery = question_router.invoke(question)
    if datasource.datasource == "analytic":
        return ANALYTIC_NODE
    else:
        return RAG_NODE
    
def analytic(state: OverallState, config: RunnableConfig) -> OverallState:
    """LangGraph node that performs analytic queries on the sqlite database."""
    return {"tool": "analytic"}

def rag(state: OverallState, config: RunnableConfig) -> OverallState:
    """LangGraph node that performs rag queries on the vector store."""
    return {"tool": "rag"}

async def format_answer(state: OverallState, config: RunnableConfig) -> OverallState:
    """LangGraph node that formats the answer."""
    logging.info(f"Formatting answer: {state}")
    
    persona = state["persona"]
    model = state["reasoning_model"]
    
    if state["tool"] == "rag":
        qa_agent = OpenAIQuestionAnswerAgent(RAGUtils(), model=model)
        res = await qa_agent.answer(state["messages"][0].content, persona=persona)
        return {"messages": [AIMessage(content=res, tool=state["tool"])]}
    else:
        res = translate_query(state["messages"][0].content, model=model)
        return {"messages": [AIMessage(content=json.dumps(res), tool=state["tool"])]}



workflow = StateGraph(OverallState, config_schema=Configuration)

workflow.add_node(ANALYTIC_NODE, analytic)
workflow.add_node(RAG_NODE, rag)
workflow.add_node(FORMAT_NODE, format_answer)

workflow.set_conditional_entry_point(route_query, {ANALYTIC_NODE: ANALYTIC_NODE, RAG_NODE: RAG_NODE})

workflow.add_edge(RAG_NODE, FORMAT_NODE)
workflow.add_edge(ANALYTIC_NODE, FORMAT_NODE)
workflow.add_edge(FORMAT_NODE, END)



workflow.compile()

graph = workflow.compile(debug=True)