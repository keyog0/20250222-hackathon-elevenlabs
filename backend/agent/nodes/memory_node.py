from typing import Dict, Any, List
from langgraph.graph import StateGraph
from ..models.context_model import Memory
from ..utils.llm_utils import LLMUtils
from ..utils.logger import logger, log_memory_update
from .output_node import AgentState

def create_memory_node(llm: LLMUtils):
    """Create a memory management node for the agent graph."""
    
    async def manage_memory(state: AgentState) -> AgentState:
        """Manage and update agent's memory systems."""
        try:
            # Add current interaction to short-term memory
            state["context"].short_term.add_interaction(
                speaker="user",
                message=state["user_input"]
            )
            
            if state["response"]:
                state["context"].short_term.add_interaction(
                    speaker=state["persona"].name,
                    message=state["response"]["response_text"],
                    metadata=state["response"]["metadata"]
                )
            
            # Log short-term memory update
            log_memory_update("short_term", {
                "history_length": len(state["context"].short_term.conversation_history),
                "last_interaction": state["context"].short_term.conversation_history[-1]
            })
            
            # Generate memory summary if conversation is significant
            if len(state["context"].short_term.conversation_history) % 5 == 0:  # Every 5 interactions
                memory_summary = await llm.generate_memory_summary(
                    state["context"].short_term.conversation_history
                )
                
                # Create and store memory
                memory = Memory(
                    content={
                        "summary": memory_summary,
                        "scenario": state["scenario"].scenario_id,
                        "emotions": state["state"].current_emotions,
                        "affinity": state["state"].affinity_score
                    },
                    importance=0.7  # Medium-high importance for regular summaries
                )
                state["context"].long_term.add_key_event(memory)
                
                # Log long-term memory update
                log_memory_update("long_term", {
                    "summary": memory_summary,
                    "importance": 0.7
                })
            
            return state
            
        except Exception as e:
            logger.error("[MemoryNode] Error managing memory:")
            logger.exception(e)
            raise
    
    return manage_memory 