import sys
import os
import asyncio
from typing import Optional
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.markdown import Markdown
from dotenv import load_dotenv

from .workflow import create_agent_workflow, run_agent, AgentState
from .utils.config_manager import ConfigManager
from .utils.llm_utils import LLMUtils
from .models.scenario_model import ScenarioModel
from .models.persona_model import PersonaModel
from .models.state_model import StateModel
from .models.context_model import ContextModel

console = Console(force_terminal=True)

class AgentCLI:
    """Simple CLI interface for interacting with the agent."""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.workflow = None
        self.state = None
        self.interaction_count = 0  # Add interaction counter
        
    def initialize(self):
        """Initialize the agent with configuration and data."""
        try:
            # Reset interaction counter
            self.interaction_count = 0
            
            # Load environment variables
            load_dotenv()
            
            # Load configuration
            config = self.config_manager.load_config()
            self.config_manager.ensure_data_directories()
            
            # Initialize LLM (will use environment variables)
            llm = LLMUtils()
            
            # Load persona and scenarios
            persona_data = self.config_manager.load_persona("persona0")
            all_scenarios = self.config_manager.load_all_scenarios()
            
            # Get initial scenario
            initial_scenario = ScenarioModel(**all_scenarios["warmup_pack"])
            initial_scenario.llm = llm  # Inject LLM into scenario
            
            # Create initial state
            persona = PersonaModel(**persona_data)
            state = StateModel(
                current_scenario_id=initial_scenario.scenario_id,
                available_scenarios=[s_id for s_id in all_scenarios.keys()]
            )
            context = ContextModel()
            
            # Initialize workflow state
            self.state = {
                "persona": persona,
                "state": state,
                "context": context,
                "scenario": initial_scenario,
                "user_input": "",
                "response": None
            }
            
            # Create workflow
            self.workflow = create_agent_workflow(llm, self.state)
            
        except Exception as e:
            console.print(f"[red]Error during initialization: {str(e)}")
            sys.exit(1)
    
    def _display_agent_response(self, response: dict):
        """Display agent's response with metadata."""
        # Display response in a panel
        console.print(Panel(
            response["response"],
            title=self.state["persona"].name,
            border_style="blue"
        ))
        
        # Display affinity and emotion status
        affinity = self.state["state"].affinity_score
        emotions = self.state["state"].current_emotions
        
        # Get current scenario requirements
        current_scenario = self.state["scenario"]
        required_affinity = current_scenario.requirements.min_affinity or 0.0
        required_emotions = current_scenario.requirements.required_emotions or {}
        
        # Create affinity progress bar
        affinity_color = "green" if affinity >= required_affinity else "yellow"
        console.print(f"\n[bold]친밀도 상태:")
        console.print(f"[{affinity_color}]▐{'█' * int(affinity/5)}{'-' * (20-int(affinity/5))}▌ {affinity:.1f}/100.0")
        if required_affinity > 0:
            console.print(f"[dim]목표 친밀도: {required_affinity}")
        
        # Display all emotions with Korean names
        all_emotions = {
            "joy": "기쁨",
            "trust": "신뢰",
            "fear": "두려움",
            "surprise": "놀람",
            "sadness": "슬픔",
            "disgust": "혐오",
            "anger": "분노",
            "anticipation": "기대"
        }
        
        console.print("\n[bold]감정 상태:")
        for emotion, kr_name in all_emotions.items():
            current_value = emotions.get(emotion, 0.0)
            required_value = required_emotions.get(emotion, 0.0)
            emotion_color = "green" if current_value >= required_value else "yellow"
            bar_length = int(current_value * 20)
            console.print(f"{kr_name}: [{emotion_color}]▐{'█' * bar_length}{'-' * (20-bar_length)}▌ {current_value:.2f}")
            if emotion in required_emotions:
                console.print(f"[dim]목표 {kr_name}: {required_value}")
        
        # Display metadata if in debug mode
        if self.debug:
            console.print("\n[bold]메타데이터:")
            console.print(response["metadata"])
    
    def _display_scenario_info(self):
        """Display current scenario information."""
        scenario = self.state["scenario"]
        console.print(Panel(
            f"{scenario.description}\n\n목표:\n" + "\n".join(f"• {goal}" for goal in scenario.goals),
            title=scenario.title,
            border_style="green"
        ))
    
    async def _get_relationship_tips(self, llm: LLMUtils) -> str:
        """Get tips for improving relationship with the agent."""
        system_prompt = f"""
        당신은 {self.state["persona"].name}입니다. {self.state["persona"].core_traits["occupation"]}이며, 다음과 같은 특성을 가지고 있습니다:

        성격:
        - 따뜻하고 설득력 있는 말투
        - 타인의 성장을 돕는 것을 좋아함
        - 긍정적이고 동기부여를 잘하는 성향
        - 공감능력이 뛰어나고 경청하는 자세

        현재 시나리오: {self.state["scenario"].title}
        시나리오 설명: {self.state["scenario"].description}
        
        현재 목표:
        {chr(10).join(f"- {goal}" for goal in self.state["scenario"].goals)}

        대화 가이드라인:
        1. 현재 시나리오의 맥락을 유지하며 대화를 이끌어가세요
        2. 각 목표를 자연스럽게 달성할 수 있도록 대화를 유도하세요
        3. 페르소나의 특성을 반영한 말투와 표현을 사용하세요
        4. 상황에 맞는 전문성과 경험을 자연스럽게 보여주세요

        지금은 사용자와의 대화를 분석하고, 시나리오 목표 달성과 관계 향상을 위한 팁을 제안하는 상황입니다.
        현재 친밀도, 감정 상태, 시나리오 맥락을 고려하여 실질적인 팁을 제안해주세요.

        답변 형식:
        [시나리오 진행 상황 & 관계 향상 팁 💫]

        현재 '{self.state["scenario"].title}' 단계에서 이런 점들을 시도해보시면 좋을 것 같아요:

        1. (시나리오 목표와 연관된 구체적인 제안)
        2. (현재 감정 상태를 고려한 관계 향상 팁)
        3. (다음 단계로의 자연스러운 진행을 위한 제안)

        화이팅하세요! 🌟
        """
        
        try:
            response = await llm.generate_response(
                system_prompt=system_prompt,
                user_prompt=str({
                    "current_affinity": self.state["state"].affinity_score,
                    "emotions": self.state["state"].current_emotions,
                    "persona": self.state["persona"].core_traits,
                    "interaction_count": self.interaction_count,
                    "scenario_progress": {
                        "current_goals": self.state["scenario"].goals,
                        "next_scenarios": self.state["scenario"].next_scenarios
                    }
                }),
                temperature=0.8
            )
            return response.content
        except Exception:
            return "앗, 죄송해요! 팁을 생성하는 중에 문제가 생겼네요. 다음에 다시 시도해볼게요! 🙏"

    async def chat_loop(self, debug: bool = False):
        """Main chat loop."""
        self.debug = debug
        
        while True:
            try:
                # Display welcome message and scenario
                console.print(f"[bold blue]{self.state['persona'].name}과의 대화를 시작합니다!")
                self._display_scenario_info()
                
                # Display initial persona introduction
                initial_greeting = f"""안녕하세요! 저는 {self.state['persona'].name}입니다.
{self.state['persona'].core_traits['occupation']}로 일하고 있어요.
{self.state['scenario'].description}
함께 좋은 시간 보내면서 이야기 나눠볼까요?"""
                
                console.print(Panel(initial_greeting, title=self.state["persona"].name, border_style="blue"))
                
                while True:
                    # Get user input
                    user_input = Prompt.ask("\n당신")
                    
                    if user_input.lower() in ['quit', 'exit', 'bye', '종료', '끝']:
                        console.print("[yellow]대화를 종료합니다. 안녕히 가세요!")
                        return
                    
                    # Process input and get response
                    response = await run_agent(self.workflow, user_input, self.state)
                    
                    # Increment interaction counter
                    self.interaction_count += 1
                    
                    # Display response
                    self._display_agent_response(response)
                    
                    # Show relationship tips every 5 interactions
                    if self.interaction_count % 5 == 0:
                        tips = await self._get_relationship_tips(self.workflow.llm)
                        console.print(Panel(
                            tips,
                            title="[bold yellow]친밀도 향상 팁",
                            border_style="yellow"
                        ))
                    
                    # Display scenario transition if it occurred
                    if response.get("metadata", {}).get("scenario_changed"):
                        self._display_scenario_info()
                        
            except KeyboardInterrupt:
                console.print("\n[yellow]사용자에 의해 중단되었습니다. 안녕히 가세요!")
                break
            except Exception as e:
                console.print(f"[red]오류 발생: {str(e)}")
                if debug:
                    import traceback
                    console.print(traceback.format_exc())

def main():
    """Main entry point."""
    cli = AgentCLI()
    cli.initialize()
    # Run the async chat loop with debug mode off
    asyncio.run(cli.chat_loop(debug=False))

if __name__ == "__main__":
    main() 