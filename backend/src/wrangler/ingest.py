import hashlib
import json
import logging
from pathlib import Path
from typing import Literal, TypedDict
from fastapi import APIRouter, HTTPException, Request
import os
from .ragUtil import RAGUtils
from fastapi import APIRouter
from agent.graph import graph
from langchain_core.messages import HumanMessage

router = APIRouter()

from langgraph.graph import StateGraph, START, END

class IngestState(TypedDict):
    status: Literal["idle", "processing", "completed", "failed"]
    

builder = StateGraph(IngestState)

@router.get("/ingest")
async def ingest():
    """ingest the data from the data folder"""
    rag = RAGUtils()
    files = rag.get_file_list()
    try:
        for file in files:
            await rag.check_or_create_document(file)   
        return {"message": "initialized!"}
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
    


@router.post("/ingest/query")
async def ingest_query(query: str, model: Literal["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"], persona: Literal["product_owner", "marketing"]):
    """Process the query using the specified model and persona"""
        # Assumng there's a function to process the query with the given model and persona
    result = await graph.ainvoke({
            "messages": [HumanMessage(content=query)],
            "reasoning_model": model,
            "persona": persona
        })
        
    if result["tool"] == "analytic":
            ans = result["messages"][1].content
            loaded_ans = json.loads(ans)
            query = loaded_ans["query"]
            result = loaded_ans["results"]
            columns_name = loaded_ans["column_names"]
            parsed_result = []
            for row in result:
                parsed_row = {}
                for i in range(len(row)):
                    parsed_row[columns_name[i]] = row[i]
                parsed_result.append(parsed_row)
            final_result = {"query": query, "result": parsed_result}
            return final_result
    else:
            ans = result["messages"][-1].content
            return {"result": result["messages"][-1].content}
