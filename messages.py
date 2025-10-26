"""
A2A Protocol Definition for Voice Agent and Knowledge Agent Communication
"""

from pydantic import BaseModel


class AgentQuery(BaseModel):
    """Query model for A2A communication from Voice Agent to Knowledge Agent"""
    user_text: str


class AgentResponse(BaseModel):
    """Response model for A2A communication from Knowledge Agent to Voice Agent"""
    script: str
    source_metadata: str
