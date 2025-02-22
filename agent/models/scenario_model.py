from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from enum import Enum
from ..utils.llm_utils import LLMUtils

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

    def update_available_scenarios(self, current_state: Any) -> List[str]:
        """Update and return available next scenarios based on current state."""
        if not self.llm:
            return [s for s in self.next_scenarios if s not in current_state.completed_scenarios]
            
        # Get conversation history from state's context
        conversation_history = []
        if hasattr(current_state, 'completed_scenarios'):
            # We received a StateModel directly
            conversation_history = []  # Default to empty if no context available
        else:
            # We received the full agent state dictionary
            conversation_history = current_state.get("context", {}).short_term.conversation_history
        
        # Use LLM to select appropriate next scenarios
        selected_scenario = self.llm.select_next_scenario(
            available_scenarios=[
                {
                    "id": s_id,
                    "title": s_id,
                    "description": "Scenario description"
                }
                for s_id in self.next_scenarios
                if (hasattr(current_state, 'completed_scenarios') and s_id not in current_state.completed_scenarios) or
                   (isinstance(current_state, dict) and s_id not in current_state["state"].completed_scenarios)
            ],
            current_state={
                "emotions": current_state.current_emotions if hasattr(current_state, 'current_emotions') 
                          else current_state["state"].current_emotions,
                "affinity": current_state.affinity_score if hasattr(current_state, 'affinity_score')
                          else current_state["state"].affinity_score
            },
            conversation_history=conversation_history
        )
        
        return [selected_scenario]  # Return the selected scenario ID

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