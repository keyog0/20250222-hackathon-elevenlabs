from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from enum import Enum
from ..utils.llm_utils import LLMUtils
from ..utils.logger import logger

class ScenarioType(str, Enum):
    CONVERSATION = "conversation"
    EVENT = "event"
    DECISION = "decision"
    REACTION = "reaction"

class ScenarioRequirement(BaseModel):
    """Defines requirements for scenario availability."""
    min_affinity: Optional[float] = None
    required_scenarios: List[str] = Field(default_factory=list)
    required_emotions: Dict[str, float] = Field(default_factory=dict)
    custom_requirements: Dict[str, Any] = Field(default_factory=dict)

class ScenarioModel(BaseModel):
    """
    Defines a scenario that the agent can participate in.
    """
    scenario_id: str
    type: ScenarioType
    title: str
    description: str
    
    # Scenario context
    location: Optional[str] = None
    time: Optional[str] = None
    participants: List[str] = Field(default_factory=list)
    
    # Scenario flow
    initial_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Initial setup and context for the scenario"
    )
    goals: List[str] = Field(
        default_factory=list,
        description="Goals to be achieved in this scenario"
    )
    
    # Progression
    requirements: ScenarioRequirement = Field(
        default_factory=ScenarioRequirement,
        description="Requirements for this scenario to be available"
    )
    next_scenarios: List[str] = Field(
        default_factory=list,
        description="Potential next scenarios"
    )
    
    # Scenario-specific state modifications
    state_modifiers: Dict[str, Any] = Field(
        default_factory=dict,
        description="How this scenario can modify agent state"
    )

    # LLM utility
    llm: Optional[LLMUtils] = None

    class Config:
        arbitrary_types_allowed = True

    def check_requirements(self, state: Any, context: Any) -> bool:
        """Check if all requirements are met to start this scenario."""
        if self.requirements.min_affinity is not None:
            if state.affinity_score < self.requirements.min_affinity:
                return False
                
        # Check if required scenarios are completed
        for req_scenario in self.requirements.required_scenarios:
            if req_scenario not in state.completed_scenarios:
                return False
        
        # Check emotional requirements
        for emotion, required_level in self.requirements.required_emotions.items():
            if state.current_emotions.get(emotion, 0.0) < required_level:
                return False
        
        return True

    def get_initial_prompt(self) -> str:
        """Generate the initial prompt for this scenario."""
        return f"Scene: {self.location or 'Unspecified location'}\n" \
               f"Time: {self.time or 'Unspecified time'}\n" \
               f"Context: {self.description}\n" \
               f"Goals: {', '.join(self.goals)}"

    def should_end_scenario(self, state: Any, context: Any) -> bool:
        """Determine if current scenario should end based on state."""
        if not self.llm:
            return False
            
        # Get conversation history from context
        conversation_history = context.short_term.conversation_history
        
        # Get current state information
        current_state = {
            "emotions": state.current_emotions,
            "affinity": state.affinity_score,
            "completed_goals": state.completed_scenarios
        }
        
        # Use LLM to evaluate scenario completion
        evaluation = self.llm.evaluate_scenario_completion(
            scenario_goals=self.goals,
            conversation_history=conversation_history,
            current_state=current_state
        )
        
        return evaluation["should_end"]

    def update_available_scenarios(self, current_state: Dict[str, Any]) -> Dict[str, Any]:
        """Update and return available scenarios based on current state."""
        try:
            # Get state object from dict if needed
            state = current_state.get("state", {})
            
            # Get completed scenarios, handling both dict and StateModel cases
            completed_scenarios = []
            if hasattr(state, "completed_scenarios"):
                completed_scenarios = state.completed_scenarios
            elif isinstance(state, dict) and "completed_scenarios" in state:
                completed_scenarios = state["completed_scenarios"]
            
            # Filter available scenarios
            available_scenarios = {}
            for scenario_id in self.next_scenarios:
                if scenario_id not in completed_scenarios:
                    available_scenarios[scenario_id] = {
                        "scenario_id": scenario_id,
                        "type": self.type,
                        "title": f"Next Scenario: {scenario_id}",
                        "description": "Transitioning to next scenario..."
                    }
            
            return available_scenarios
            
        except Exception as e:
            logger.error(f"Error updating available scenarios: {str(e)}")
            # Return empty dict as fallback
            return {}

    async def get_state_modifications(self, interaction_result: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate state modifications based on interaction results."""
        if not self.llm:
            modifications = {}
            for key, modifier in self.state_modifiers.items():
                if isinstance(modifier, dict):
                    if "condition" in modifier and "value" in modifier:
                        if eval(modifier["condition"], {"result": interaction_result}):
                            modifications[key] = modifier["value"]
            return modifications
            
        # Use LLM to suggest state modifications
        system_prompt = """
        Based on the interaction results, suggest appropriate modifications to the agent's state.
        Consider:
        1. Emotional changes
        2. Relationship development
        3. Goal progress
        4. Character growth
        
        Return a JSON object with suggested state modifications.
        """
        
        response = await self.llm.generate_response(
            system_prompt=system_prompt,
            user_prompt=str(interaction_result),
            temperature=0.3
        )
        
        # Parse and return modifications
        import json
        return json.loads(response.content) 