from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class PersonaModel(BaseModel):
    """
    Defines the core personality traits of the agent that remain constant throughout interactions.
    """
    name: str
    core_traits: Dict[str, Any] = Field(
        description="Core personality traits that define the character"
    )
    background: Dict[str, Any] = Field(
        description="Character's background information"
    )
    speech_style: Dict[str, Any] = Field(
        description="Character's way of speaking and communication preferences"
    )
    values: Dict[str, Any] = Field(
        description="Character's core values and beliefs"
    )
    
    def get_trait(self, trait_name: str) -> Optional[Any]:
        """Retrieve a specific trait value."""
        return self.core_traits.get(trait_name)

    def get_speech_characteristic(self, characteristic: str) -> Optional[Any]:
        """Get specific speech characteristic."""
        return self.speech_style.get(characteristic)

    def is_action_aligned(self, action: str) -> bool:
        """Check if an action aligns with character's values and personality."""
        # Implementation will depend on specific personality rules
        return True  # Placeholder 