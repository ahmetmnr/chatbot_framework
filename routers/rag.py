from fastapi import APIRouter, Depends, HTTPException
from typing import List

from api.schemas import RAGConfig
from api.dependencies import get_assistant
from core.rag.simple_rag import SimpleRAG

router = APIRouter(
    prefix="/rag",
    tags=["rag"]
)

@router.post("/{assistant_name}/add")
async def add_rag_to_assistant(
    assistant_name: str,
    rag_config: RAGConfig,
    documents: dict,
    assistant = Depends(get_assistant)
):
    rag_system = SimpleRAG(rag_config.name, documents)
    assistant.add_rag_system(
        rag_system,
        name=rag_config.name,
        weight=rag_config.weight,
        enabled=rag_config.enabled
    )
    return {"message": f"RAG system {rag_config.name} added to assistant {assistant_name}"}

@router.post("/{assistant_name}/{rag_name}/toggle")
async def toggle_rag_system(
    assistant_name: str,
    rag_name: str,
    enable: bool,
    assistant = Depends(get_assistant)
):
    if enable:
        assistant.enable_rag_system(rag_name)
    else:
        assistant.disable_rag_system(rag_name)
    return {"message": f"RAG system {rag_name} {'enabled' if enable else 'disabled'}"} 