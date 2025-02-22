from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class Memory(BaseModel):
    """Base class for memory entries."""
    timestamp: datetime = Field(default_factory=datetime.now)
    content: Dict[str, Any]
    importance: float = Field(default=0.0, ge=0.0, le=1.0)

class ShortTermMemory(BaseModel):
    """Manages current scenario conversation history."""
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    current_context: Dict[str, Any] = Field(default_factory=dict)
    
    def add_interaction(self, speaker: str, message: str, metadata: Optional[Dict] = None) -> None:
        """Add a new interaction to conversation history."""
        self.conversation_history.append({
            "timestamp": datetime.now(),
            "speaker": speaker,
            "message": message,
            "metadata": metadata or {}
        })

    def get_recent_context(self, n_messages: int = 5) -> List[Dict[str, Any]]:
        """Get the n most recent messages."""
        return self.conversation_history[-n_messages:]

class LongTermMemory(BaseModel):
    """Manages memories from completed scenarios and important events."""
    scenario_memories: Dict[str, List[Memory]] = Field(default_factory=dict)
    key_events: List[Memory] = Field(default_factory=list)
    relationship_development: Dict[str, Any] = Field(default_factory=dict)

    def add_scenario_memory(self, scenario_id: str, memory: Memory) -> None:
        """Add a memory from a completed scenario."""
        if scenario_id not in self.scenario_memories:
            self.scenario_memories[scenario_id] = []
        self.scenario_memories[scenario_id].append(memory)

    def add_key_event(self, event: Memory) -> None:
        """Add an important event to long-term memory."""
        self.key_events.append(event)

    def update_relationship_development(self, aspect: str, value: Any) -> None:
        """Update relationship development tracking."""
        self.relationship_development[aspect] = value

class ContextModel(BaseModel):
    """
    Manages both short-term and long-term memory systems.
    """
    short_term: ShortTermMemory = Field(default_factory=ShortTermMemory)
    long_term: LongTermMemory = Field(default_factory=LongTermMemory)

    def transfer_to_long_term(self, scenario_id: str) -> None:
        """Transfer relevant short-term memories to long-term memory."""
        # Create a summary of the scenario
        summary = {
            "scenario_id": scenario_id,
            "conversation_summary": self.short_term.conversation_history,
            "context": self.short_term.current_context
        }
        
        # Create a new memory and store it
        memory = Memory(
            content=summary,
            importance=0.8  # High importance for scenario completions
        )
        self.long_term.add_scenario_memory(scenario_id, memory)
        
        # Clear short-term memory for next scenario
        self.short_term = ShortTermMemory()

    def get_relevant_memories(self, query: Dict[str, Any]) -> List[Memory]:
        """Retrieve relevant memories based on query parameters."""
        # Implementation will depend on specific memory retrieval logic
        return []  # Placeholder 