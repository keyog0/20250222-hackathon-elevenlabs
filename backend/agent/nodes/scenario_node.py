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
                current_scenario, state["context"].short_term.conversation_history, state["state"]
            )

            # Log completion analysis
            logger.info(f"[Scenario] Completion Analysis: {completion_analysis}")

            # Update goals based on completion analysis
            for achieved_goal in completion_analysis.get("goals_achieved", []):
                state["state"].update_progress(achieved_goal)
            
            # Update response metadata with goal progress
            if state["response"] and "metadata" in state["response"]:
                state["response"]["metadata"].update({
                    "goals_achieved": state["state"].completed_goals,
                    "remaining_goals": state["state"].get_remaining_goals(),
                    "current_progress": state["state"].get_progress(),
                    "total_goals": state["state"].total_goals,
                    "new_achievements": completion_analysis.get("goals_achieved", [])
                })

                # Add goal progress message to response
                goal_progress = "\n\n📊 목표 진행 상황:\n"
                if state["state"].completed_goals:
                    goal_progress += "\n✅ 달성한 목표:\n"
                    for goal in state["state"].completed_goals:
                        goal_progress += f"  - {goal}\n"
                
                goal_progress += "\n🎯 남은 목표:\n"
                for goal in state["state"].get_remaining_goals():
                    goal_progress += f"  - {goal}\n"

                if completion_analysis.get("goals_achieved"):
                    goal_progress += "\n🎉 이번 대화에서 달성한 목표:\n"
                    for goal in completion_analysis["goals_achieved"]:
                        goal_progress += f"  - {goal}\n"

                state["response"]["response_text"] += goal_progress
            
            # Check for failure conditions
            if (
                not completion_analysis["requirements_status"]["affinity"]["met"]
                or not completion_analysis["requirements_status"]["emotions"]["met"]
            ):
                # Increment failure counter
                if state["state"].increment_failure_counter():
                    # Max failures reached, suggest restart or end
                    logger.warning("[Scenario] Maximum failures reached")

                    # Update response metadata to indicate failure
                    if state["response"] and "metadata" in state["response"]:
                        state["response"]["metadata"].update(
                            {
                                "max_failures_reached": True,
                                "blocking_factors": completion_analysis["feedback"]["improvement_needed"],
                                "restart_suggested": True,
                            }
                        )

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
                        blocking_factors=", ".join(completion_analysis["feedback"]["improvement_needed"]),
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
                    current_scenario, state["state"], state["context"], completion_analysis
                )

                if next_scenario:
                    old_scenario_id = current_scenario.scenario_id

                    # Initialize new scenario
                    state["scenario"] = next_scenario
                    state["state"].current_scenario_id = next_scenario.scenario_id
                    
                    # Set new scenario goals
                    state["state"].set_scenario_goals(next_scenario.goals)

                    # Update metadata to indicate scenario change
                    if state["response"] and "metadata" in state["response"]:
                        state["response"]["metadata"].update(
                            {
                                "scenario_changed": True,
                                "previous_scenario": old_scenario_id,
                                "completion_reason": completion_analysis["reason"],
                                "goals_achieved": completion_analysis["goals_achieved"],
                            }
                        )

                    # Log scenario transition
                    log_scenario_update(old_scenario_id, next_scenario.scenario_id)
                    logger.info(f"[Scenario] New Goals: {next_scenario.goals}")

            return state

        except Exception as e:
            logger.error("[ScenarioNode] Error managing scenario:")
            logger.exception(e)
            raise

    async def _analyze_scenario_completion(
        scenario: ScenarioModel, conversation_history: List[Dict[str, Any]], state: Any
    ) -> Dict[str, Any]:
        """Analyze if the current scenario should end."""
        system_prompt = """
        현재 시나리오의 목표 달성도와 완료 여부를 분석하세요.
        각 목표에 대해 대화 내용을 기반으로 달성 여부를 판단하고, 상세한 피드백을 제공하세요.

        시나리오 목표 달성 기준:
        1. 각 목표별 구체적인 달성 조건:
           - 대화 내용에서 해당 목표와 관련된 명확한 증거가 있어야 함
           - 사용자의 반응이 긍정적이고 참여도가 높아야 함
           - 목표가 자연스럽게 달성되었다고 판단되어야 함

        2. 감정과 친밀도 요구사항:
           - 현재 감정 상태가 목표 달성에 적합한지
           - 친밀도가 충분한 수준인지
           - 대화의 전반적인 톤이 긍정적인지

        3. 대화 품질 평가:
           - 대화가 자연스럽게 흐르는지
           - 상호작용이 효과적인지
           - 목표 달성을 위한 진전이 있는지

        다음 형식으로 응답하세요 (마크다운 없이 순수 JSON):
        {
            "should_end": boolean,
            "reason": string,
            "goals_achieved": string[],  // 이번 분석에서 새로 달성된 목표들
            "remaining_goals": string[],  // 아직 달성되지 않은 목표들
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
                "depth": float,        // 0-1 사이 값
                "engagement": float,    // 0-1 사이 값
                "potential": float      // 0-1 사이 값
            },
            "feedback": {
                "success_points": string[],  // 잘 된 점들
                "improvement_needed": string[],  // 개선이 필요한 점들
                "next_steps": string[]  // 다음 단계 제안
            }
        }

        각 목표의 달성 여부를 판단할 때는 다음을 고려하세요:
        1. 명시적 증거: 대화에서 직접적으로 확인할 수 있는 증거
        2. 암묵적 증거: 대화의 톤, 맥락, 사용자의 반응에서 유추할 수 있는 증거
        3. 진행 상태: 부분적으로 달성된 목표의 경우, 완전한 달성까지 필요한 요소
        """

        analysis_context = {
            "goals": scenario.goals,
            "conversation": conversation_history[-5:],  # Last 5 interactions
            "emotions": state.current_emotions,
            "affinity": state.affinity_score,
            "requirements": scenario.requirements,
            "completed_goals": state.completed_goals,  # Add completed goals for context
            "progress_percentage": state.get_progress()  # Add current progress
        }

        try:
            response = await llm.generate_response(
                system_prompt=system_prompt, user_prompt=str(analysis_context), temperature=0.3
            )

            # Parse the response as JSON
            import json

            analysis = json.loads(response.content)

            # Log detailed analysis
            logger.info(f"[Scenario Analysis] Requirements Status: {analysis['requirements_status']}")
            logger.info(f"[Scenario Analysis] Goals Progress: {len(analysis['goals_achieved'])}/{len(scenario.goals)}")
            logger.info(f"[Scenario Analysis] Feedback: {analysis['feedback']}")

            # If requirements not met, provide specific feedback
            if not analysis["requirements_status"]["affinity"]["met"]:
                logger.info(
                    f"[Scenario Blocked] Affinity too low: {analysis['requirements_status']['affinity']['current']} < {analysis['requirements_status']['affinity']['required']}"
                )
            if not analysis["requirements_status"]["emotions"]["met"]:
                logger.info(
                    f"[Scenario Blocked] Required emotions not met: {analysis['requirements_status']['emotions']}"
                )

            return analysis

        except json.JSONDecodeError:
            logger.error(f"Failed to parse completion analysis: {response.content}")
            return {
                "should_end": False,
                "reason": "Analysis failed",
                "goals_achieved": [],
                "remaining_goals": scenario.goals,
                "requirements_status": {"affinity": {"met": False}, "emotions": {"met": False}},
                "conversation_quality": {"depth": 0.0, "engagement": 0.0, "potential": 0.0},
                "feedback": {
                    "success_points": [],
                    "improvement_needed": ["시나리오 분석에 실패했습니다"],
                    "next_steps": ["다시 시도해주세요"],
                },
            }

    async def _select_next_scenario(
        current_scenario: ScenarioModel,
        state: Any,
        context: Any,
        completion_analysis: Dict[str, Any]
    ) -> Optional[ScenarioModel]:
        """Select next scenario based on current state."""
        try:
            # Get available scenarios
            available_scenarios = current_scenario.update_available_scenarios({"state": state})
            
            if not available_scenarios:
                return None
            
            # Get next scenario response from LLM
            next_scenario_response = await current_scenario.llm.select_next_scenario(
                available_scenarios=list(available_scenarios.values()),
                current_state=state.dict(),
                conversation_history=[{
                    "speaker": "user" if msg.get("is_user") else "agent",
                    "message": msg.get("content", "")
                } for msg in context.short_term.conversation_history]
            )
            
            # Parse the response to get scenario_id
            try:
                import json
                response_data = json.loads(next_scenario_response)
                next_scenario_id = response_data.get("scenario_id")
                
                if next_scenario_id and next_scenario_id in available_scenarios:
                    # Create new scenario model
                    return ScenarioModel(
                        **available_scenarios[next_scenario_id],
                        llm=current_scenario.llm
                    )
            except Exception as e:
                logger.error(f"Error parsing next scenario response: {str(e)}")
            
            # Fallback to first available scenario if selection fails
            logger.warning("[ScenarioNode] Failed to select next scenario, using fallback")
            fallback_id = list(available_scenarios.keys())[0]
            return ScenarioModel(
                **available_scenarios[fallback_id],
                llm=current_scenario.llm
            )
            
        except Exception as e:
            logger.error(f"[ScenarioNode] Error selecting next scenario: {str(e)}")
            raise

    return manage_scenario
