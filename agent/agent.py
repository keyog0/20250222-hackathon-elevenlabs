from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from .models.persona_model import PersonaModel
from .models.state_model import StateModel
from .models.context_model import ContextModel
from .models.scenario_model import ScenarioModel
from .nodes.output_node import OutputNode
from .nodes.feedback_node import FeedbackNode
from .utils.llm_utils import LLMUtils

class Agent(BaseModel):
    """
    Main agent class that orchestrates all components and manages the interaction flow.
    """
    # Core components
    persona: PersonaModel
    state: StateModel
    context: ContextModel
    
    # Current scenario
    current_scenario: ScenarioModel
    available_scenarios: Dict[str, ScenarioModel] = Field(default_factory=dict)
    
    # Processing nodes
    output_node: OutputNode
    feedback_node: FeedbackNode

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def initialize(
        cls,
        persona_data: Dict[str, Any],
        initial_scenario: ScenarioModel,
        available_scenarios: Dict[str, ScenarioModel]
    ) -> "Agent":
        """
        Initialize a new agent with persona data and initial scenario.
        """
        # Create LLM instance
        llm = LLMUtils()
        
        # Initialize components
        persona = PersonaModel(**persona_data)
        state = StateModel(
            current_scenario_id=initial_scenario.scenario_id,
            available_scenarios=[s_id for s_id in available_scenarios.keys()]
        )
        context = ContextModel()
        
        # Initialize processing nodes with LLM
        output_node = OutputNode(llm=llm)
        feedback_node = FeedbackNode(llm=llm)
        
        # Create agent instance
        agent = cls(
            persona=persona,
            state=state,
            context=context,
            current_scenario=initial_scenario,
            available_scenarios=available_scenarios,
            output_node=output_node,
            feedback_node=feedback_node
        )
        
        return agent

    def process_input(self, user_input: str, additional_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process user input and generate response.
        """
        # Generate response
        response_data = self.output_node.generate_response(
            user_input=user_input,
            persona=self.persona,
            state=self.state,
            context=self.context,
            scenario=self.current_scenario,
            additional_context=additional_context
        )
        
        # Process feedback and update state
        self.state, self.context = self.feedback_node.process_feedback(
            user_input=user_input,
            current_state=self.state,
            context=self.context,
            interaction_metadata=response_data["metadata"]
        )
        
        # Check scenario progression
        self._check_scenario_progression()
        
        return {
            "response": response_data["response_text"],
            "metadata": {
                "emotional_state": self.state.current_emotions,
                "affinity_score": self.state.affinity_score,
                "current_scenario": self.current_scenario.title,
                "scenario_changed": False  # Will be updated by _check_scenario_progression
            }
        }

    def _check_scenario_progression(self) -> None:
        """
        Check if current scenario should end and handle scenario transition.
        """
        if self.current_scenario.should_end_scenario(self.state, self.context):
            # Transfer short-term memory to long-term memory
            self.context.transfer_to_long_term(self.current_scenario.scenario_id)
            
            # Mark current scenario as complete
            self.state.complete_current_scenario()
            
            # Get next available scenarios
            available_next = self.current_scenario.update_available_scenarios(self.state)
            
            # Filter scenarios based on requirements
            valid_next = [
                s_id for s_id in available_next
                if self.available_scenarios[s_id].check_requirements(self.state, self.context)
            ]
            
            if valid_next:
                # Select next scenario (can be enhanced with more sophisticated selection)
                next_scenario_id = valid_next[0]
                self.current_scenario = self.available_scenarios[next_scenario_id]
                self.state.current_scenario_id = next_scenario_id

    def get_current_state(self) -> Dict[str, Any]:
        """
        Get current state of the agent.
        """
        return {
            "emotional_state": self.state.current_emotions,
            "affinity_score": self.state.affinity_score,
            "current_scenario": self.current_scenario.title,
            "completed_scenarios": self.state.completed_scenarios
        }

    def get_available_scenarios(self) -> List[Dict[str, Any]]:
        """
        Get list of available next scenarios.
        """
        available = self.current_scenario.update_available_scenarios(self.state)
        return [
            {
                "id": s_id,
                "title": self.available_scenarios[s_id].title,
                "description": self.available_scenarios[s_id].description
            }
            for s_id in available
            if self.available_scenarios[s_id].check_requirements(self.state, self.context)
        ] 