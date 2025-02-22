from typing import Dict, Any, Optional, TypedDict
from langgraph.graph import StateGraph
from ..models.state_model import StateModel, EmotionCategory
from ..models.context_model import ContextModel, Memory
from ..utils.llm_utils import LLMUtils
from ..utils.logger import logger, log_memory_update
from .output_node import AgentState

def create_feedback_node(llm: LLMUtils):
    """Create a feedback node for the agent graph."""
    
    async def process_feedback(state: AgentState) -> AgentState:
        """Process user feedback and update state and context."""
        try:
            # Analyze user input for sentiment and feedback using LLM
            feedback_analysis = await _analyze_feedback(state["user_input"], llm)
            
            # Update user impressions
            _update_user_impressions(state["state"], feedback_analysis)
            
            # Add to context if significant
            if feedback_analysis.get("significance", 0) > 0.5:  # threshold for significant interactions
                _add_to_long_term_memory(
                    state["context"], 
                    feedback_analysis, 
                    state["response"]["metadata"] if state["response"] else {}
                )
            
            return state
            
        except Exception as e:
            logger.error("[FeedbackNode] Error processing feedback:")
            logger.exception(e)
            raise

    async def _analyze_feedback(user_input: str, llm: LLMUtils) -> Dict[str, Any]:
        """Analyze user input for emotional content and feedback using LLM."""
        system_prompt = """
        사용자의 입력을 분석하여 다음 형식의 JSON으로 응답하세요:
        {
            "sentiment": float (-1에서 1 사이, 부정적에서 긍정적),
            "appropriateness": float (0에서 1 사이, 대화의 적절성),
            "respect_level": float (0에서 1 사이, 예의 수준),
            "emotional_alignment": float (0에서 1 사이, 페르소나와의 감정적 일치도),
            "significance": float (0에서 1 사이, 대화의 중요도),
            "topics": string[]
        }
        """
        
        try:
            response = await llm.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_input,
                temperature=0.3,
                max_tokens=1000
            )
            
            try:
                import json
                return json.loads(response.content)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse LLM response: {response.content}")
                return {
                    "sentiment": 0,
                    "appropriateness": 0.5,
                    "respect_level": 0.5,
                    "emotional_alignment": 0.5,
                    "significance": 0.5,
                    "topics": []
                }
        except Exception as e:
            logger.error(f"Error analyzing feedback: {str(e)}")
            raise

    def _update_user_impressions(
        state: StateModel,
        feedback_analysis: Dict[str, Any]
    ) -> None:
        """Update impressions about the user based on their feedback."""
        for topic in feedback_analysis.get("topics", []):
            state.add_user_impression(
                f"interest_{topic}",
                feedback_analysis.get("sentiment", 0)
            )
        
        # Add impressions about user's behavior
        state.add_user_impression(
            "respect_level",
            feedback_analysis.get("respect_level", 0.5)
        )
        state.add_user_impression(
            "appropriateness",
            feedback_analysis.get("appropriateness", 0.5)
        )

    def _add_to_long_term_memory(
        context: ContextModel,
        feedback_analysis: Dict[str, Any],
        interaction_metadata: Dict[str, Any]
    ) -> None:
        """Add significant interactions to long-term memory."""
        memory = Memory(
            content={
                "feedback": feedback_analysis,
                "metadata": interaction_metadata
            },
            importance=feedback_analysis.get("significance", 0.5)
        )
        context.long_term.add_key_event(memory)

    return process_feedback 