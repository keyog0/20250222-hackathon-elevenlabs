from typing import Dict, Any, List, Optional
import os
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

class LLMResponse(BaseModel):
    """Structure for LLM response data."""
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class LLMUtils:
    """Utility class for OpenAI API interactions."""
    
    def __init__(self, api_key: Optional[str] = None):
        # Use provided API key or get from environment
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found in environment variables")
            
        self.client = AsyncOpenAI(api_key=self.api_key)
        # Default model for general tasks
        self.default_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        # Advanced model for emotion analysis
        self.emotion_model = "gpt-4o-mini"

    def _clean_json_response(self, content: str) -> str:
        """Clean JSON response from markdown formatting and other artifacts."""
        # Remove markdown code block if present
        if "```" in content:
            # Extract content between code blocks
            import re
            match = re.search(r"```(?:json)?(.*?)```", content, re.DOTALL)
            if match:
                content = match.group(1)
            else:
                # If no matching end block, just remove start block
                content = content.replace("```json", "").replace("```", "")
        
        # Remove any leading/trailing whitespace
        content = content.strip()
        
        return content

    async def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        functions: Optional[List[Dict[str, Any]]] = None,
        use_emotion_model: bool = False
    ) -> LLMResponse:
        """
        Generate a response using OpenAI API asynchronously.
        """
        try:
            # Add scenario context reminder to system prompt
            scenario_context = """
            대화 시 주의사항:
            1. 현재 시나리오의 맥락과 목표를 항상 고려하며 대화하세요
            2. 시나리오 진행에 도움이 되는 방향으로 대화를 이끌어가세요
            3. 페르소나의 특성과 전문성을 자연스럽게 보여주세요
            4. 불필요하게 주제에서 벗어나지 않도록 주의하세요
            """
            
            enhanced_prompt = system_prompt + "\n" + scenario_context + "\n\nPlease respond in Korean, using appropriate honorifics and natural Korean expressions."
            
            messages = [
                {"role": "system", "content": enhanced_prompt},
                {"role": "user", "content": user_prompt}
            ]

            completion = await self.client.chat.completions.create(
                model=self.emotion_model if use_emotion_model else self.default_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                functions=functions
            )

            return LLMResponse(
                content=self._clean_json_response(completion.choices[0].message.content),
                metadata={
                    "finish_reason": completion.choices[0].finish_reason,
                    "model": completion.model,
                    "usage": completion.usage.model_dump() if completion.usage else {}
                }
            )
        except Exception as e:
            raise Exception(f"Error generating response: {str(e)}")

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment and emotions in text asynchronously.
        Uses the advanced model (gpt-4o) for better analysis.
        """
        system_prompt = """
        다음 텍스트의 감정과 정서를 분석하세요.
        다음 구조의 JSON 객체로 반환하세요:
        {
            "sentiment": float (-1에서 1 사이),
            "emotions": {감정: float (0에서 1 사이)},
            "topics": 관련 주제 리스트,
            "significance": float (0에서 1 사이)
        }
        """
        
        try:
            response = await self.generate_response(
                system_prompt=system_prompt,
                user_prompt=text,
                temperature=0.3,
                use_emotion_model=True  # Use gpt-4o for emotion analysis
            )
            
            # Parse the response as JSON
            import json
            return json.loads(response.content)
        except Exception as e:
            raise Exception(f"Error analyzing sentiment: {str(e)}")

    async def generate_memory_summary(self, conversation_history: List[Dict[str, Any]]) -> str:
        """
        Generate a summary of conversation history for long-term memory asynchronously.
        """
        system_prompt = """
        이 대화의 주요 포인트와 감정적 순간들을 요약하세요.
        향후 상호작용을 위해 기억해야 할 중요한 정보에 초점을 맞추세요.
        관계나 이해도의 중요한 변화를 포함하세요.
        """
        
        try:
            # Convert conversation history to readable format
            conversation_text = "\n".join(
                f"{msg['speaker']}: {msg['message']}" 
                for msg in conversation_history
            )
            
            response = await self.generate_response(
                system_prompt=system_prompt,
                user_prompt=conversation_text,
                temperature=0.5
            )
            
            return response.content
        except Exception as e:
            raise Exception(f"Error generating memory summary: {str(e)}")

    async def evaluate_scenario_completion(
        self,
        scenario_goals: List[str],
        conversation_history: List[Dict[str, Any]],
        current_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate whether current scenario should end based on goals and state asynchronously.
        """
        system_prompt = """
        다음 기준에 따라 현재 시나리오를 종료해야 하는지 평가하세요:
        1. 시나리오의 목표가 달성되었나요?
        2. 대화가 자연스러운 결론에 도달했나요?
        3. 새로운 시나리오로 전환하기 좋은 기회인가요?
        
        다음 구조의 JSON 객체로 반환하세요:
        {
            "should_end": boolean,
            "reason": string,
            "goal_completion": float (0에서 1 사이),
            "suggested_next_topics": string 리스트
        }
        """
        
        try:
            context = {
                "goals": scenario_goals,
                "conversation": conversation_history,
                "current_state": current_state
            }
            
            response = await self.generate_response(
                system_prompt=system_prompt,
                user_prompt=str(context),
                temperature=0.3
            )
            
            # Parse the response as JSON
            import json
            return json.loads(response.content)
        except Exception as e:
            raise Exception(f"Error evaluating scenario completion: {str(e)}")

    async def select_next_scenario(
        self,
        available_scenarios: List[Dict[str, Any]],
        current_state: Dict[str, Any],
        conversation_history: List[Dict[str, Any]]
    ) -> str:
        """
        Select the most appropriate next scenario based on current context asynchronously.
        """
        system_prompt = """
        다음 기준에 따라 가장 적절한 다음 시나리오를 선택하세요:
        1. 현재 감정 상태와 친밀도
        2. 최근 대화 주제와 관심사
        3. 자연스러운 진행과 스토리 흐름
        
        선택한 시나리오 ID와 간단한 설명을 반환하세요.
        """
        
        try:
            context = {
                "available_scenarios": available_scenarios,
                "current_state": current_state,
                "recent_conversation": conversation_history[-5:]  # Last 5 messages
            }
            
            response = await self.generate_response(
                system_prompt=system_prompt,
                user_prompt=str(context),
                temperature=0.7
            )
            
            return response.content  # Will contain scenario_id and explanation
        except Exception as e:
            raise Exception(f"Error selecting next scenario: {str(e)}") 