from typing import Dict
from core.models.assistant import Assistant
from fastapi import HTTPException

# Global assistants dictionary
assistants: Dict[str, Assistant] = {}

def get_assistant(name: str) -> Assistant:
    """Get assistant by name or raise 404"""
    if name not in assistants:
        raise HTTPException(status_code=404, detail="Assistant not found")
    return assistants[name] 