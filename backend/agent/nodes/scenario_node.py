from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph
from ..models.scenario_model import ScenarioModel
from ..utils.llm_utils import LLMUtils
from ..utils.logger import logger, log_scenario_update
from .output_node import AgentState

def create_scenario_node(llm: LLMUtils):
    """Create a scenario management node for the agent graph."""
    
    async def manage_scenario(state: AgentState) -> AgentState:
        """Check and update scenario progression."""
        try:
            current_scenario = state["scenario"]
            
            # Analyze scenario completion
            completion_analysis = await _analyze_scenario_completion(
                current_scenario,
                state["context"].short_term.conversation_history,
                state["state"]
            )
            
            # Log completion analysis
            logger.info(f"[Scenario] Completion Analysis: {completion_analysis}")
            
            # Check for failure conditions
            if not completion_analysis["requirements_status"]["affinity"]["met"] or \
               not completion_analysis["requirements_status"]["emotions"]["met"]:
                # Increment failure counter
                if state["state"].increment_failure_counter():
                    # Max failures reached, suggest restart or end
                    logger.warning("[Scenario] Maximum failures reached")
                    
                    # Update response metadata to indicate failure
                    if state["response"] and "metadata" in state["response"]:
                        state["response"]["metadata"].update({
                            "max_failures_reached": True,
                            "blocking_factors": completion_analysis["feedback"]["improvement_needed"],
                            "restart_suggested": True
                        })
                    
                    # Add failure message to response
                    failure_message = """
                    죄송하지만, 대화가 원하는 방향으로 진행되지 않고 있습니다.
                    
                    현재 상황:
                    - 친밀도: {current_affinity:.1f}/{required_affinity:.1f}
                    - 부족한 점: {blocking_factors}
                    
                    다시 시작하시겠습니까? ('재시작' 또는 '종료' 를 입력해주세요)
                    """.format(
                        current_affinity=completion_analysis["requirements_status"]["affinity"]["current"],
                        required_affinity=completion_analysis["requirements_status"]["affinity"]["required"],
                        blocking_factors=", ".join(completion_analysis["feedback"]["improvement_needed"])
                    )
                    
                    if state["response"]:
                        state["response"]["response_text"] = failure_message
                    
                    return state
            else:
                # Requirements met, reset failure counter
                state["state"].reset_failure_counter()
            
            # Check if current scenario should end
            if completion_analysis["should_end"]:
                # Log scenario completion
                logger.info(f"[Scenario] Completed: {current_scenario.scenario_id}")
                logger.info(f"[Scenario] Completion Reason: {completion_analysis['reason']}")
                
                # Transfer short-term memory to long-term memory
                state["context"].transfer_to_long_term(current_scenario.scenario_id)
                
                # Mark current scenario as complete
                state["state"].complete_current_scenario()
                
                # Get next scenario
                next_scenario = await _select_next_scenario(
                    current_scenario,
                    state["state"],
                    state["context"],
                    completion_analysis
                )
                
                if next_scenario:
                    old_scenario_id = current_scenario.scenario_id
                    
                    # Initialize new scenario
                    state["scenario"] = next_scenario
                    state["state"].current_scenario_id = next_scenario.scenario_id
                    
                    # Update metadata to indicate scenario change
                    if state["response"] and "metadata" in state["response"]:
                        state["response"]["metadata"].update({
                            "scenario_changed": True,
                            "previous_scenario": old_scenario_id,
                            "completion_reason": completion_analysis["reason"],
                            "goals_achieved": completion_analysis["goals_achieved"]
                        })
                    
                    # Log scenario transition
                    log_scenario_update(old_scenario_id, next_scenario.scenario_id)
                    logger.info(f"[Scenario] New Goals: {next_scenario.goals}")
            
            return state
            
        except Exception as e:
            logger.error("[ScenarioNode] Error managing scenario:")
            logger.exception(e)
            raise

    async def _analyze_scenario_completion(
        scenario: ScenarioModel,
        conversation_history: List[Dict[str, Any]],
        state: Any
    ) -> Dict[str, Any]:
        """Analyze if the current scenario should end."""
        system_prompt = """
        현재 시나리오의 완료 여부를 분석하세요. 다음 조건들을 확인하고 상세한 피드백을 제공하세요.
        마크다운 코드 블록(```) 없이 순수 JSON 형식으로만 응답해주세요.

        1. 필수 조건:
           - 현재 친밀도(affinity)가 목표치에 도달했는지
           - 필요한 감정 상태(emotions)가 충족되었는지
           - 이전 시나리오가 완료되었는지

        2. 시나리오 목표:
           - 각 목표의 달성 여부
           - 남은 목표와 달성하기 위해 필요한 것

        3. 대화 품질:
           - 대화의 깊이와 의미
           - 상호 이해도
           - 향후 발전 가능성

        다음 형식으로 응답하세요 (마크다운 없이 순수 JSON):
        {
            "should_end": boolean,
            "reason": string,
            "goals_achieved": string[],
            "remaining_goals": string[],
            "requirements_status": {
                "affinity": {
                    "current": float,
                    "required": float,
                    "met": boolean
                },
                "emotions": {
                    "current": object,
                    "required": object,
                    "met": boolean
                }
            },
            "conversation_quality": {
                "depth": float,
                "engagement": float,
                "potential": float
            },
            "feedback": {
                "success_points": string[],
                "improvement_needed": string[],
                "next_steps": string[]
            }
        }
        """
        
        analysis_context = {
            "goals": scenario.goals,
            "conversation": conversation_history[-5:],  # Last 5 interactions
            "emotions": state.current_emotions,
            "affinity": state.affinity_score,
            "requirements": scenario.requirements
        }
        
        try:
            response = await llm.generate_response(
                system_prompt=system_prompt,
                user_prompt=str(analysis_context),
                temperature=0.3
            )
            
            # Parse the response as JSON
            import json
            analysis = json.loads(response.content)
            
            # Log detailed analysis
            logger.info(f"[Scenario Analysis] Requirements Status: {analysis['requirements_status']}")
            logger.info(f"[Scenario Analysis] Goals Progress: {len(analysis['goals_achieved'])}/{len(scenario.goals)}")
            logger.info(f"[Scenario Analysis] Feedback: {analysis['feedback']}")
            
            # If requirements not met, provide specific feedback
            if not analysis['requirements_status']['affinity']['met']:
                logger.info(f"[Scenario Blocked] Affinity too low: {analysis['requirements_status']['affinity']['current']} < {analysis['requirements_status']['affinity']['required']}")
            if not analysis['requirements_status']['emotions']['met']:
                logger.info(f"[Scenario Blocked] Required emotions not met: {analysis['requirements_status']['emotions']}")
            
            return analysis
            
        except json.JSONDecodeError:
            logger.error(f"Failed to parse completion analysis: {response.content}")
            return {
                "should_end": False,
                "reason": "Analysis failed",
                "goals_achieved": [],
                "remaining_goals": scenario.goals,
                "requirements_status": {
                    "affinity": {"met": False},
                    "emotions": {"met": False}
                },
                "conversation_quality": {
                    "depth": 0.0,
                    "engagement": 0.0,
                    "potential": 0.0
                },
                "feedback": {
                    "success_points": [],
                    "improvement_needed": ["시나리오 분석에 실패했습니다"],
                    "next_steps": ["다시 시도해주세요"]
                }
            }

    async def _select_next_scenario(
        current_scenario: ScenarioModel,
        state: Any,
        context: Any,
        completion_analysis: Dict[str, Any]
    ) -> Optional[ScenarioModel]:
        """Select the most appropriate next scenario."""
        try:
            # Get available scenarios
            available_next = current_scenario.update_available_scenarios({
                "state": state,
                "context": context
            })
            
            # Filter based on requirements
            valid_next = [
                s_id for s_id in available_next
                if current_scenario.check_requirements(state, context)
            ]
            
            if not valid_next:
                logger.warning("[Scenario] No valid next scenarios available")
                return None
            
            # Analyze best next scenario
            system_prompt = """
            다음 시나리오를 선택하세요. 다음을 고려하세요:
            1. 현재 감정 상태와 관계 수준
            2. 이전 대화의 주제와 흐름
            3. 달성한 목표와 남은 목표
            4. 자연스러운 전개

            가장 적절한 시나리오 ID를 반환하세요.
            """
            
            selection_context = {
                "available_scenarios": valid_next,
                "current_state": {
                    "emotions": state.current_emotions,
                    "affinity": state.affinity_score,
                    "completed_goals": completion_analysis["goals_achieved"]
                },
                "conversation_state": completion_analysis.get("conversation_quality", {})
            }
            
            response = await llm.generate_response(
                system_prompt=system_prompt,
                user_prompt=str(selection_context),
                temperature=0.3
            )
            
            selected_id = response.content.strip()
            if selected_id in valid_next:
                # Create new scenario instance
                return ScenarioModel(
                    scenario_id=selected_id,
                    llm=llm,
                    type=current_scenario.type,  # Preserve scenario type
                    title=f"New Scenario: {selected_id}",
                    description="Transitioning to new scenario..."
                )
            
            # Fallback to first valid scenario
            logger.warning(f"[Scenario] Selected scenario {selected_id} not valid, using fallback")
            return ScenarioModel(
                scenario_id=valid_next[0],
                llm=llm,
                type=current_scenario.type,
                title=f"New Scenario: {valid_next[0]}",
                description="Transitioning to new scenario..."
            )
        except Exception as e:
            logger.error(f"[ScenarioNode] Error selecting next scenario: {str(e)}")
            logger.exception(e)
            return None

    return manage_scenario 