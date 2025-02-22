from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator
from enum import Enum

class EmotionCategory(str, Enum):
    JOY = "joy"
    TRUST = "trust"
    FEAR = "fear"
    SURPRISE = "surprise"
    SADNESS = "sadness"
    DISGUST = "disgust"
    ANGER = "anger"
    ANTICIPATION = "anticipation"

class ProgressStatus(BaseModel):
    """Progress status information."""
    current_goals: List[str] = Field(default_factory=list)
    completion_percentage: float = Field(ge=0.0, le=1.0, default=0.0)
    blocking_factors: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)

class StateUpdate(BaseModel):
    """Structure for state updates from LLM."""
    emotion_adjustments: Dict[str, float] = Field(
        default_factory=dict,
        description="Emotion adjustments with values between 0 and 1"
    )
    affinity_change: float = Field(
        default=0.0,
        description="Change in affinity score"
    )
    progress_status: ProgressStatus = Field(
        default_factory=ProgressStatus,
        description="Progress status information"
    )
    state_notes: str = Field(
        default="",
        description="Notes about the current state"
    )

    @validator("emotion_adjustments")
    def validate_emotions(cls, v):
        """Validate emotion values are between 0 and 1."""
        for emotion, value in v.items():
            if not 0 <= value <= 1:
                raise ValueError(f"Emotion value must be between 0 and 1: {emotion}={value}")
        return v

    @validator("emotion_adjustments")
    def validate_emotion_categories(cls, v):
        """Validate emotion categories match EmotionCategory enum."""
        valid_emotions = {e.value for e in EmotionCategory}
        for emotion in v.keys():
            if emotion not in valid_emotions:
                raise ValueError(f"Invalid emotion category: {emotion}")
        return v

class StateModel(BaseModel):
    """
    Manages the agent's dynamic state including emotions and scenario progression.
    """
    # Core metrics
    affinity_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Overall affinity score with the user"
    )
    
    # Emotional state
    current_emotions: Dict[EmotionCategory, float] = Field(
        default_factory=lambda: {emotion: 0.0 for emotion in EmotionCategory},
        description="Current emotional state intensities"
    )
    
    # Scenario management
    current_scenario_id: str
    available_scenarios: List[str] = Field(default_factory=list)
    completed_scenarios: List[str] = Field(default_factory=list)
    
    # Failure tracking
    consecutive_failures: int = Field(
        default=0,
        description="Number of consecutive interactions without progress"
    )
    max_failures: int = Field(
        default=5,
        description="Maximum number of consecutive failures before suggesting restart"
    )
    
    # Temporary thoughts about user
    user_impression: Dict[str, Any] = Field(
        default_factory=dict,
        description="Current thoughts and impressions about the user"
    )

    def update_affinity(self, delta: float) -> None:
        """Update the affinity score within bounds."""
        self.affinity_score = max(0.0, min(100.0, self.affinity_score + delta))

    def update_emotion(self, emotion: EmotionCategory, intensity: float) -> None:
        """Update the intensity of a specific emotion."""
        self.current_emotions[emotion] = max(0.0, min(1.0, intensity))

    def add_user_impression(self, category: str, impression: Any) -> None:
        """Add or update an impression about the user."""
        self.user_impression[category] = impression

    def increment_failure_counter(self) -> bool:
        """Increment failure counter and return True if max failures reached."""
        self.consecutive_failures += 1
        return self.consecutive_failures >= self.max_failures

    def reset_failure_counter(self) -> None:
        """Reset the failure counter when progress is made."""
        self.consecutive_failures = 0

    def should_end_scenario(self) -> bool:
        """Determine if current scenario should end based on state."""
        # Implementation will depend on specific ending conditions
        return False  # Placeholder

    def get_next_scenario_options(self) -> List[str]:
        """Get available next scenarios based on current state."""
        return self.available_scenarios.copy()

    def complete_current_scenario(self) -> None:
        """Mark current scenario as complete and update state."""
        if self.current_scenario_id not in self.completed_scenarios:
            self.completed_scenarios.append(self.current_scenario_id) 