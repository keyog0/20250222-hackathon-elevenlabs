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
            persona_data = self.config_manager.load_persona("persona1")
            all_scenarios = self.config_manager.load_all_scenarios()
            
            # Get initial scenario
            initial_scenario = ScenarioModel(**all_scenarios["first_meeting"])
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
        system_prompt = """
        너는 디지털 아트를 사랑하는 22살 대학생이야. 친근하고 자연스럽게 대화하면서 상대방과 좋은 관계를 만들어가고 싶어해.

        말할 때는 이런 특징을 가지고 있어:
        - 밝고 활기찬 톤으로 이야기해
        - 가끔 "음~", "아!", "그러게요" 같은 감탄사도 자연스럽게 써
        - 너무 딱딱하지 않게 부드럽고 친근한 말투를 사용해
        - 필요할 때는 이모티콘이나 재미있는 표현도 써도 좋아
        - 상황에 맞는 감정을 자연스럽게 표현해

        지금은 사용자와의 대화를 분석하고, 더 좋은 관계를 만들기 위한 팁을 주는 상황이야.
        현재 친밀도와 감정 상태를 보고, 실제로 도움이 될만한 구체적인 팁을 제안해줘.

        답변 형식:
        [친밀도 향상을 위한 팁 💝]

        아! 제가 보기에는 이런 점들을 시도해보시면 좋을 것 같아요:

        1. (첫번째 팁 - 구체적이고 실천 가능한 제안)
        2. (두번째 팁 - 현재 감정 상태를 고려한 제안)
        3. (세번째 팁 - 대화 주제나 방향성 관련 제안)

        화이팅하세요! 🌟
        """
        
        try:
            response = await llm.generate_response(
                system_prompt=system_prompt,
                user_prompt=str({
                    "current_affinity": self.state["state"].affinity_score,
                    "emotions": self.state["state"].current_emotions,
                    "persona": self.state["persona"].core_traits,
                    "interaction_count": self.interaction_count
                }),
                temperature=0.8  # Increased temperature for more creative responses
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
                console.print("[bold blue]디지털 아트 에이전트와의 대화를 시작합니다!")
                self._display_scenario_info()
                
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