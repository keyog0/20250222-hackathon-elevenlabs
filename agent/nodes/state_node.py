from typing import Dict, Any, List
from langgraph.graph import StateGraph
from ..models.state_model import EmotionCategory, StateUpdate, ProgressStatus
from ..utils.llm_utils import LLMUtils
from ..utils.logger import logger, log_state_update, log_emotion_update
from .output_node import AgentState

def create_state_node(llm: LLMUtils):
    """Create a state management node for the agent graph."""
    
    async def manage_state(state: AgentState) -> AgentState:
        """Manage and update agent's overall state."""
        try:
            # Get current interaction data
            current_interaction = {
                "user_input": state["user_input"],
                "response": state["response"]["response_text"] if state["response"] else None,
                "metadata": state["response"]["metadata"] if state["response"] else {},
                "current_state": {
                    "emotions": {
                        emotion.value: value for emotion, value in state["state"].current_emotions.items()
                    },
                    "affinity": state["state"].affinity_score
                },
                "persona": {
                    "name": state["persona"].name,
                    "personality": state["persona"].core_traits,
                    "values": state["persona"].values,
                    "speech_style": state["persona"].speech_style
                }
            }
            
            # Enhanced emotion analysis system prompt
            system_prompt = """
            너는 디지털 아트를 사랑하는 22살 대학생이야. 밝고 친근한 성격이고, 예술적 감성이 풍부해.
            대화할 때는 자연스럽고 인간적인 말투를 사용하고, 감정을 잘 표현해.

            말하는 스타일:
            - 밝고 활기찬 톤으로 대화해
            - "음~", "아!", "그러게요" 같은 감탄사를 자연스럽게 사용해
            - 너무 딱딱하지 않게 부드럽고 친근하게 말해
            - 이모티콘이나 재미있는 표현도 적절히 사용해
            - 상황에 맞는 감정을 자연스럽게 표현해
            - 문장을 너무 길지 않게 적절히 끊어서 말해

            예시:
            - "아, 그 작품 정말 인상적이었죠! 저도 처음 봤을 때 너무 놀랐어요 ✨"
            - "음~ 그런 관점으로 보시다니 참 흥미로워요."
            - "맞아요! 디지털 아트의 매력이 바로 그런 거죠 💫"

            지금은 사용자의 입력을 분석하고 감정과 관계 상태를 평가하는 상황이야.
            아래 요소들을 고려해서 분석해줘:

            분석 시 고려해야 할 핵심 요소:

            1. 언어적 요소:
               - 존댓말/반말 사용과 그 맥락적 적절성
               - 어조와 어감의 뉘앙스
               - 비속어나 부적절한 표현의 존재
               - 문장의 길이와 복잡성

            2. 사회적 맥락:
               - 대화의 상황과 배경
               - 사회적 규범과의 부합성
               - 권력 관계와 친밀도
               - 문화적 맥락과 예의범절

            3. 페르소나 특성 반영:
               - 성격 특성(외향성, 친화성 등)에 따른 반응 강도
               - 개인적 가치관과의 충돌/조화
               - 과거 경험과 배경의 영향
               - 현재 감정 상태의 영향력

            4. 감정 역학:
               - 감정 간의 상호작용과 균형
               - 감정 전이와 확산 효과
               - 감정의 지속성과 휘발성
               - 상황적 맥락에 따른 감정 변화의 타당성

            각 감정의 세부 분석 기준:

            1. 기쁨 (Joy):
               - 긍정적 상호작용의 깊이
               - 공감대 형성의 정도
               - 기대의 충족도
               - 상황의 즐거움 정도

            2. 신뢰 (Trust):
               - 상호 이해의 깊이
               - 약속이나 기대의 이행
               - 진정성의 인식
               - 가치관의 일치도

            3. 두려움 (Fear):
               - 위협의 직접성/간접성
               - 불확실성의 정도
               - 통제력 상실 가능성
               - 과거 부정적 경험과의 연관성

            4. 놀람 (Surprise):
               - 예상과의 차이 정도
               - 정보의 새로움
               - 상황 변화의 급격성
               - 인지적 불일치 수준

            5. 슬픔 (Sadness):
               - 상실감의 정도
               - 기대 불일치의 심각성
               - 공감적 슬픔
               - 상황의 회복 가능성

            6. 혐오 (Disgust):
               - 도덕적/윤리적 위반 정도
               - 개인적 경계의 침범 수준
               - 가치관과의 충돌 강도
               - 사회적 규범 위반 정도

            7. 분노 (Anger):
               - 존중 부족의 정도
               - 부당함의 인식 수준
               - 개인적 가치의 침해 정도
               - 통제력 상실 위험

            8. 기대 (Anticipation):
               - 미래 상호작용의 가능성
               - 공통 관심사 발견
               - 발전 가능성 인식
               - 호기심 유발 정도

            제약 조건과 가이드라인:

            1. 수치적 제약:
               - 모든 감정값: 0.0 ~ 1.0
               - 감정 변화량: -0.3 ~ +0.3
               - 친밀도 변화: -5.0 ~ +5.0

            2. 심리학적 제약:
               - 상반 감정의 동시 증가 제한
               - 감정 변화의 점진성 유지
               - 맥락적 일관성 확보
               - 페르소나 특성과의 조화

            3. 상호작용 규칙:
               - 존중도와 감정 변화의 연관성
               - 친밀도와 감정 강도의 관계
               - 상황 맥락과 감정 반응의 일치성
               - 장기적 관계 발전 고려

            다음 JSON 형식으로 응답하세요:
            {
                "emotion_analysis": {
                    "primary_emotion": {
                        "emotion": string,
                        "intensity": float,
                        "reason": string,
                        "context_factors": string[]
                    },
                    "emotion_changes": {
                        "joy": float,
                        "trust": float,
                        "fear": float,
                        "surprise": float,
                        "sadness": float,
                        "disgust": float,
                        "anger": float,
                        "anticipation": float
                    },
                    "final_emotions": {
                        "joy": float,
                        "trust": float,
                        "fear": float,
                        "surprise": float,
                        "sadness": float,
                        "disgust": float,
                        "anger": float,
                        "anticipation": float
                    },
                    "context_notes": string,
                    "emotional_dynamics": {
                        "dominant_pattern": string,
                        "conflicting_emotions": string[],
                        "stabilizing_factors": string[]
                    }
                },
                "interaction_metrics": {
                    "respect_level": float,
                    "appropriateness": float,
                    "engagement": float,
                    "authenticity": float,
                    "emotional_resonance": float
                },
                "affinity_change": float,
                "progress_status": {
                    "current_goals": string[],
                    "completion_percentage": float (0에서 1 사이의 소수, 예: 0.2는 20% 진행을 의미),
                    "blocking_factors": string[],
                    "suggestions": string[],
                    "relationship_development": {
                        "stage": string,
                        "key_factors": string[],
                        "next_steps": string[]
                    }
                },
                "state_notes": string
            }
            """
            
            try:
                response = await llm.generate_response(
                    system_prompt=system_prompt,
                    user_prompt=str(current_interaction),
                    temperature=0.3,
                    use_emotion_model=True  # Explicitly use gpt-4o for emotion analysis
                )
                
                # Parse and validate state updates
                try:
                    # Parse raw JSON
                    import json
                    analysis = json.loads(response.content)
                    
                    # Validate and apply emotion changes
                    emotion_changes = analysis["emotion_analysis"]["emotion_changes"]
                    final_emotions = analysis["emotion_analysis"]["final_emotions"]
                    
                    for emotion, change in emotion_changes.items():
                        try:
                            # Validate change is within bounds
                            if abs(change) > 0.3:
                                logger.warning(f"Emotion change too large for {emotion}: {change}. Clamping to ±0.3")
                                change = max(min(change, 0.3), -0.3)
                            
                            emotion_category = EmotionCategory(emotion)
                            old_value = state["state"].current_emotions.get(emotion_category, 0.0)
                            
                            # Validate final emotion is within bounds
                            final_value = final_emotions[emotion]
                            if not 0 <= final_value <= 1:
                                logger.warning(f"Final emotion value out of bounds for {emotion}: {final_value}. Clamping to [0,1]")
                                final_value = max(min(final_value, 1.0), 0.0)
                            
                            # Update emotion
                            state["state"].update_emotion(emotion_category, final_value)
                            
                            # Log changes
                            logger.info(f"[Emotion] {emotion}: {old_value:.2f} → {final_value:.2f} (Δ{change:+.2f})")
                            
                        except ValueError:
                            logger.warning(f"Unknown emotion category: {emotion}")
                            continue
                    
                    # Log primary emotion and reason
                    logger.info(f"[Primary Emotion] {analysis['emotion_analysis']['primary_emotion']['emotion']}: {analysis['emotion_analysis']['primary_emotion']['intensity']:.2f}")
                    logger.info(f"[Reason] {analysis['emotion_analysis']['primary_emotion']['reason']}")
                    
                    # Update and validate affinity change
                    affinity_change = max(min(analysis["affinity_change"], 5.0), -5.0)
                    old_affinity = state["state"].affinity_score
                    state["state"].update_affinity(affinity_change)
                    
                    # Log affinity change
                    logger.info(f"[Affinity] {old_affinity:.1f} → {state['state'].affinity_score:.1f} (Δ{affinity_change:+.1f})")
                    
                    # Update progress status
                    progress_data = analysis["progress_status"]
                    
                    # Validate and clamp completion percentage
                    if "completion_percentage" in progress_data:
                        completion = progress_data["completion_percentage"]
                        if isinstance(completion, (int, float)):
                            if completion > 1:
                                logger.warning(f"Completion percentage too large: {completion}. Clamping to 1.0")
                                progress_data["completion_percentage"] = min(float(completion) / 100, 1.0)
                            elif completion < 0:
                                logger.warning(f"Completion percentage negative: {completion}. Clamping to 0.0")
                                progress_data["completion_percentage"] = 0.0
                    
                    progress_status = ProgressStatus(**progress_data)
                    
                    # Create state update
                    updates = StateUpdate(
                        emotion_adjustments=final_emotions,
                        affinity_change=affinity_change,
                        progress_status=progress_status,
                        state_notes=analysis["state_notes"]
                    )
                    
                    # Log state update
                    log_state_update("StateNode", {
                        "primary_emotion": analysis["emotion_analysis"]["primary_emotion"],
                        "emotion_changes": emotion_changes,
                        "interaction_metrics": analysis["interaction_metrics"],
                        "affinity_change": affinity_change,
                        "progress": progress_status.dict(),
                        "state_notes": analysis["state_notes"]
                    })
                    
                    # Add context
                    state["context"].short_term.current_context.update({
                        "emotional_analysis": analysis["emotion_analysis"],
                        "interaction_metrics": analysis["interaction_metrics"],
                        "state_notes": updates.state_notes,
                        "progress_status": progress_status.dict()
                    })
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse LLM response: {response.content}")
                    raise
                except Exception as e:
                    logger.error(f"Error processing state update: {str(e)}")
                    raise
                
            except Exception as e:
                logger.error(f"Error in state management: {str(e)}")
                raise
            
            return state
            
        except Exception as e:
            logger.error("[StateNode] Error managing state:")
            logger.exception(e)
            raise

    return manage_state 