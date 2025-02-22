from sqlalchemy.orm import Session
from backend.agent.models.context_model import ContextModel
from backend.agent.models.persona_model import PersonaModel
from backend.agent.models.scenario_model import ScenarioModel
from backend.agent.models.state_model import StateModel
from backend.src.schemas.message import Emotion, MessageType, RoomMessage, EmotionState, ScenarioInfo
from backend.src.config import settings
import base64
import httpx
from typing import Dict, Any, Optional

from backend.agent.workflow import create_agent_workflow, run_agent
from backend.agent.utils.config_manager import ConfigManager
from backend.agent.utils.llm_utils import LLMUtils
from backend.agent.utils.logger import logger


class AgentService:
    def __init__(self, db: Session):
        self.db = db
        self.config_manager = ConfigManager()
        self.workflow = None
        self.state = None
        self.interaction_count = 0
        self.initialize()

    def initialize(self):
        """Initialize the agent with configuration and data."""
        try:
            # Reset interaction counter
            self.interaction_count = 0
            
            # Load configuration
            config = self.config_manager.load_config()
            self.config_manager.ensure_data_directories()
            
            # Initialize LLM
            llm = LLMUtils()
            
            # Load persona and scenarios
            persona_data = self.config_manager.load_persona("persona0")  # Using the ENFJ persona
            all_scenarios = self.config_manager.load_all_scenarios()
            
            # Get initial scenario
            initial_scenario = ScenarioModel(**all_scenarios["warmup_pack"])
            initial_scenario.llm = llm
            
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
            logger.error(f"Error during initialization: {str(e)}")
            raise

    def _get_dominant_emotion(self, emotions: Dict[str, float]) -> str:
        """Get the dominant emotion from emotion state."""
        return max(emotions.items(), key=lambda x: x[1])[0]

    def _create_emotion_state(self, emotions: Dict[str, float]) -> EmotionState:
        """Convert emotion dictionary to EmotionState model."""
        return EmotionState(**emotions)

    def _create_scenario_info(self, scenario: Any) -> ScenarioInfo:
        """Create ScenarioInfo from current scenario."""
        progress = 0.0
        try:
            if hasattr(self.state["context"], "short_term"):
                if hasattr(self.state["context"].short_term, "progress"):
                    progress = max(0.0, float(self.state["context"].short_term.progress))
        except Exception:
            pass
            
        return ScenarioInfo(
            title=scenario.title,
            description=scenario.description,
            goals=scenario.goals,
            current_progress=progress
        )

    def _threshold_affinity(self, value: float) -> float:
        """Apply threshold to affinity score"""
        if abs(value) < 1.0:  # 작은 변화는 무시
            return 0.0
        if value > 100.0:
            return 100.0
        if value < 0.0:
            return 0.0
        return value

    def _threshold_emotions(self, emotions: Dict[str, float]) -> Dict[str, float]:
        """Apply threshold to emotion values"""
        return {k: EmotionState.threshold_emotion(v) for k, v in emotions.items()}

    async def get_agent_response(self, message: RoomMessage) -> RoomMessage:
        """Generate agent response with all necessary information."""
        try:
            # Increment interaction counter
            self.interaction_count += 1
            
            # Get response from workflow
            response = await run_agent(self.workflow, message.content, self.state)
            
            # Get current emotion state and affinity
            emotion_state = self._threshold_emotions(self.state["state"].current_emotions)
            affinity = self._threshold_affinity(self.state["state"].affinity_score)
            
            # Get relationship tips if needed
            tips = None
            if self.interaction_count % 5 == 0:  # Every 5 interactions
                tips = await self._get_relationship_tips()
            
            # Convert text to audio
            audio_bytes = await self.convert_text_to_audio(response["response"])
            audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
            
            # Create response message
            return RoomMessage(
                type=MessageType.text,
                content=response["response"],
                sender="agent",
                emotion=Emotion(
                    emotion=self._get_dominant_emotion(emotion_state),
                    likeability=affinity / 100,  # Convert to 0-1 scale
                    emotion_state=self._create_emotion_state(emotion_state)
                ),
                audio_data=audio_base64,
                scenario_info=self._create_scenario_info(self.state["scenario"]),
                metadata=response["metadata"],
                tips=tips,
                requires_user_action=response.get("metadata", {}).get("scenario_changed", False)
            )
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise

    async def _get_relationship_tips(self) -> Optional[str]:
        """Generate relationship tips using the workflow's LLM."""
        try:
            system_prompt = f"""
            당신은 {self.state["persona"].name}입니다. {self.state["persona"].core_traits["occupation"]}이며, 다음과 같은 특성을 가지고 있습니다:

            현재 시나리오: {self.state["scenario"].title}
            시나리오 설명: {self.state["scenario"].description}
            
            현재 목표:
            {chr(10).join(f"- {goal}" for goal in self.state["scenario"].goals)}

            현재 상황을 분석하고, 관계 향상을 위한 구체적인 팁을 제안해주세요.
            """
            
            response = await self.workflow.llm.generate_response(
                system_prompt=system_prompt,
                user_prompt=str({
                    "current_affinity": self.state["state"].affinity_score,
                    "emotions": self.state["state"].current_emotions,
                    "interaction_count": self.interaction_count
                }),
                temperature=0.7
            )
            return response.content
        except Exception:
            logger.error("Error generating relationship tips")
            return None

    async def convert_text_to_audio(self, text: str) -> bytes:
        """Convert text to audio using ElevenLabs API."""
        voice_id = "JBFqnCBsd6RMkjVDRZzb"
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "xi-api-key": settings.ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
        }
        query_params = {"output_format": "mp3_44100_128"}
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.75,
                "similarity_boost": 0.75,
            },
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data, params=query_params)
        if response.status_code == 200:
            return response.content
        else:
            raise Exception(f"Elevenlabs API 호출 실패: {response.status_code} {response.text}")


class LLMAgentService:
    def __init__(self, db: Session):
        self.db = db
