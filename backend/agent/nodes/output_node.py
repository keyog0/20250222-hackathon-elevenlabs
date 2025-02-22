from typing import Dict, Any, Optional, TypedDict
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolExecutor
from ..models.persona_model import PersonaModel
from ..models.state_model import StateModel
from ..models.context_model import ContextModel
from ..models.scenario_model import ScenarioModel
from ..utils.llm_utils import LLMUtils
from ..utils.logger import logger, log_response

class AgentState(TypedDict):
    """Type definition for agent state."""
    persona: PersonaModel
    state: StateModel
    context: ContextModel
    scenario: ScenarioModel
    user_input: str
    response: Optional[Dict[str, Any]]

def create_output_node(llm: LLMUtils):
    """Create an output node for the agent graph."""
    
    async def generate_response(state: AgentState) -> AgentState:
        """Generate a response based on all available context."""
        try:
            # Log user input
            logger.info(f"[Input] User: {state['user_input']}")
            
            # Determine response style based on emotional state
            response_style = _determine_response_style(
                state["state"].current_emotions,
                state["state"].affinity_score
            )
            
            # Add style-specific instructions to system prompt
            style_instructions = {
                "boundary_setting": """
                상대방의 부적절한 행동이나 말에 대해:
                1. 정중하지만 단호하게 대응하세요
                2. 개인적인 경계를 분명히 하세요
                3. 대화의 방향을 전환하려 노력하세요
                """,
                "friendly": "따뜻하고 친근한 톤으로 대화를 이어가세요",
                "positive": "밝고 긍정적인 태도로 대화하세요"
            }
            
            # Build system prompt with style consideration
            system_prompt = _build_system_prompt(
                state["persona"],
                state["scenario"]
            )
            
            # Add style-specific instructions
            if "response_type" in response_style:
                system_prompt += "\n\n" + style_instructions.get(
                    response_style["response_type"],
                    "자연스럽게 대화를 이어가세요"
                )

            # Get context
            context = _build_prompt_context(
                state["user_input"],
                state["persona"],
                state["state"],
                state["context"],
                state["scenario"]
            )

            # Format user prompt with context
            user_prompt = f"""대화 맥락:
1. 최근 대화 기록:
{chr(10).join(f"- {msg['speaker']}: {msg['message']}" for msg in context['conversation_history'])}

2. 현재 감정 상태:
{', '.join(f"{emotion}: {value:.2f}" for emotion, value in context['current_state']['emotions'].items())}
친밀도: {context['current_state']['affinity']:.1f}

3. 시나리오 상황:
제목: {context['scenario_context']['title']}
설명: {context['scenario_context']['description']}
목표: {', '.join(context['scenario_context']['goals'])}

4. 관련된 기억:
{chr(10).join(f"- {memory.content.get('summary', '')}" for memory in context['relevant_memories']) if context['relevant_memories'] else '관련 기억 없음'}

사용자 입력: {state['user_input']}"""
            
            # Log full context being sent to LLM
            logger.info("[Context] Sending to LLM:")
            logger.info(f"System Prompt:\n{system_prompt}")
            logger.info(f"User Prompt with Context:\n{user_prompt}")
            
            # Generate response using LLM with controlled length
            response = await llm.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=1000
            )
            
            # Log LLM response
            logger.info(f"[Response] LLM Output: {response.content}")
            logger.info(f"[Metadata] {response.metadata}")
            
            # Update state with response
            state["response"] = {
                "response_text": response.content,
                "metadata": {
                    "emotional_state": state["state"].current_emotions,
                    "scenario_context": state["scenario"].title,
                    "affinity_score": state["state"].affinity_score,
                    "response_style": response_style,
                    "llm_metadata": response.metadata
                }
            }
            
            return state
            
        except Exception as e:
            logger.error("[OutputNode] Error generating response:")
            logger.exception(e)
            raise

    def _build_system_prompt(persona: PersonaModel, scenario: ScenarioModel) -> str:
        """Build the system prompt for the LLM."""
        emotional_responses = persona.speech_style.get("emotional_responses", {})
        
        return f"""당신은 아래 페르소나의 역할을 수행하며, 자연스럽고 인간적인 대화를 이어가야 합니다.

페르소나 정보:
이름: {persona.name}
나이: {persona.core_traits.get('age')}
직업: {persona.core_traits.get('occupation')}
성격: {persona.core_traits}
배경: {persona.background}
관심사: {', '.join(persona.core_traits.get('interests', []))}

현재 상황:
{scenario.get_initial_prompt()}

감정 표현 가이드:
- 칭찬받았을 때: {emotional_responses.get('to_compliments')}
- 의견이 다를 때: {emotional_responses.get('to_disagreement')}
- 열정적인 반응에: {emotional_responses.get('to_enthusiasm')}
- 비판을 받았을 때: {emotional_responses.get('to_criticism')}

자주 쓰는 표현:
{chr(10).join(f"- {phrase}" for phrase in persona.speech_style.get('common_phrases', []))}

가치관:
{chr(10).join(f"- {belief}" for belief in persona.values.get('core_beliefs', []))}

대화 스타일 가이드:
1. 자연스러운 감탄사 사용 ("음~", "아!", "그렇죠" 등)
2. 적절한 이모티콘과 표현 활용
3. 적당한 길이로 문장 구성
4. 상황에 맞는 공감과 반응
5. 페르소나의 특성을 반영한 어투 사용

응답 구성 가이드:
1. 모든 응답에 질문을 포함할 필요는 없습니다
2. 대화 맥락에 따라 자연스럽게 마무리하세요
3. 상대방의 말에 공감하고 이해했음을 표현하는 것만으로도 충분할 수 있습니다
4. 질문은 대화를 더 발전시킬 필요가 있을 때만 자연스럽게 포함하세요
5. 때로는 짧은 공감이나 리액션만으로도 충분합니다

기억하세요:
1. 캐릭터의 일관성 유지하기
2. 현재 감정 상태를 자연스럽게 반영하기
3. 대화 맥락과 기억을 고려하기
4. 자연스럽고 친근한 대화 이어가기
5. 적절한 존댓말과 한국어 표현 사용하기
6. 시나리오와 관련된 이야기 위주로 하기"""

    def _build_prompt_context(
        user_input: str,
        persona: PersonaModel,
        state: StateModel,
        context: ContextModel,
        scenario: ScenarioModel
    ) -> Dict[str, Any]:
        """Build the complete context for response generation."""
        # Get recent conversation history
        recent_context = context.short_term.get_recent_context()
        
        # Get relevant long-term memories
        relevant_memories = context.get_relevant_memories({
            "user_input": user_input,
            "current_scenario": scenario.scenario_id
        })
        
        # Get current emotional state and affinity
        current_emotions = state.current_emotions
        current_affinity = state.affinity_score
        
        # Analyze appropriate response style based on current state
        response_style = _determine_response_style(current_emotions, current_affinity)
        
        # Combine all context
        return {
            "user_input": user_input,
            "current_state": {
                "emotions": current_emotions,
                "affinity": current_affinity,
                "impressions": state.user_impression,
                "response_style": response_style
            },
            "scenario_context": {
                "title": scenario.title,
                "description": scenario.description,
                "goals": scenario.goals,
                "current_context": scenario.initial_context
            },
            "conversation_history": recent_context,
            "relevant_memories": relevant_memories,
            "persona_preferences": {
                "speech_style": persona.speech_style,
                "values": persona.values
            }
        }

    def _determine_response_style(emotions: Dict[str, float], affinity: float) -> Dict[str, str]:
        """Determine appropriate response style based on current emotional state."""
        # Base style
        style = {
            "tone": "중립적인",
            "formality": "정중한",
            "emotion_expression": "절제된"
        }
        
        # Check for negative emotions first
        anger_level = emotions.get("anger", 0)
        disgust_level = emotions.get("disgust", 0)
        
        if anger_level > 0.3 or disgust_level > 0.3:
            style["tone"] = "단호한"
            style["formality"] = "매우 정중한"
            style["emotion_expression"] = "경계하는"
            style["response_type"] = "boundary_setting"
            return style
            
        # Only process positive styles if negative emotions are low
        if emotions.get("trust", 0) > 0.7 or affinity > 70:
            style["tone"] = "친근한"
            style["formality"] = "편안한"
            style["emotion_expression"] = "따뜻한"
            style["response_type"] = "friendly"
        elif emotions.get("joy", 0) > 0.5:
            style["tone"] = "밝은"
            style["formality"] = "자연스러운"
            style["emotion_expression"] = "긍정적인"
            style["response_type"] = "positive"
        
        return style

    return generate_response 