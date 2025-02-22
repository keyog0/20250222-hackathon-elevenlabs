from typing import Dict, Any, List, Optional, Set, ClassVar
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
        description="Emotion adjustments with values between -1 and 1"
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
        """Validate emotion values are between -1 and 1."""
        for emotion, value in v.items():
            if not -1 <= value <= 1:
                raise ValueError(f"Emotion value must be between -1 and 1: {emotion}={value}")
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
    # Class-level constants with proper type annotations
    POSITIVE_EMOTIONS: ClassVar[Set[EmotionCategory]] = {EmotionCategory.JOY, EmotionCategory.TRUST, EmotionCategory.ANTICIPATION}
    NEGATIVE_EMOTIONS: ClassVar[Set[EmotionCategory]] = {EmotionCategory.FEAR, EmotionCategory.SADNESS, EmotionCategory.DISGUST, EmotionCategory.ANGER}
    
    # Core metrics
    affinity_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Overall affinity score with the user"
    )
    
    # Conversation counter
    conversation_count: int = Field(
        default=0,
        description="Number of conversations in current scenario"
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

    # Progress tracking
    progress_status: ProgressStatus = Field(
        default_factory=ProgressStatus,
        description="Current progress status of the scenario"
    )
    
    # Goals tracking
    completed_goals: List[str] = Field(
        default_factory=list,
        description="List of completed goals in current scenario"
    )
    total_goals: List[str] = Field(
        default_factory=list,
        description="List of all goals in current scenario"
    )

    def calculate_affinity_from_emotions(self) -> float:
        """Calculate affinity score based on positive and negative emotions."""
        positive_sum = sum(self.current_emotions[emotion] for emotion in self.POSITIVE_EMOTIONS)
        negative_sum = sum(self.current_emotions[emotion] for emotion in self.NEGATIVE_EMOTIONS)
        
        # Calculate raw affinity (can be negative)
        raw_affinity = positive_sum - negative_sum
        
        # Scale to 0-100 range (assuming emotion values are between -1 and 1)
        # Maximum possible difference is 3 - (-4) = 7 (3 positive emotions minus 4 negative emotions)
        scaled_affinity = ((raw_affinity + 7) / 14) * 100
        
        # Ensure within bounds
        return max(0.0, min(100.0, scaled_affinity))

    def update_emotion(self, emotion: EmotionCategory, intensity: float) -> None:
        """Update the intensity of a specific emotion and recalculate affinity."""
        # Update emotion intensity
        self.current_emotions[emotion] = max(-1.0, min(1.0, intensity))
        
        # Recalculate and update affinity score
        self.affinity_score = self.calculate_affinity_from_emotions()

    def update_affinity(self, delta: float) -> None:
        """
        This method is deprecated. Affinity is now automatically calculated from emotions.
        """
        pass  # Affinity is now derived from emotions

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
        # End scenario if conversation count reaches 3
        if self.conversation_count >= 3:
            return True
        # End scenario if all goals are completed
        if self.progress_status.completion_percentage >= 1.0:
            return True
        # End scenario if max failures reached
        if self.consecutive_failures >= self.max_failures:
            return True
        return False

    def get_next_scenario_options(self) -> List[str]:
        """Get available next scenarios based on current state."""
        return self.available_scenarios.copy()

    def complete_current_scenario(self) -> None:
        """Mark current scenario as complete and update state."""
        if self.current_scenario_id not in self.completed_scenarios:
            self.completed_scenarios.append(self.current_scenario_id)

    def update_progress(self, completed_goal: str) -> None:
        """Update progress when a goal is completed."""
        if completed_goal not in self.completed_goals and completed_goal in self.total_goals:
            self.completed_goals.append(completed_goal)
            # Update progress percentage
            self.progress_status.completion_percentage = len(self.completed_goals) / len(self.total_goals)
            # Update current goals
            self.progress_status.current_goals = [
                goal for goal in self.total_goals 
                if goal not in self.completed_goals
            ]
            # Reset failure counter as progress was made
            self.reset_failure_counter()

    def set_scenario_goals(self, goals: List[str]) -> None:
        """Set the goals for the current scenario."""
        self.total_goals = goals.copy()
        self.completed_goals = []
        self.progress_status.current_goals = goals.copy()
        self.progress_status.completion_percentage = 0.0

    def get_progress(self) -> float:
        """Get current progress percentage."""
        return self.progress_status.completion_percentage

    def get_remaining_goals(self) -> List[str]:
        """Get list of remaining goals."""
        return self.progress_status.current_goals.copy()

    def increment_conversation_count(self) -> None:
        """Increment the conversation counter."""
        self.conversation_count += 1

    def reset_conversation_count(self) -> None:
        """Reset the conversation counter when changing scenarios."""
        self.conversation_count = 0 