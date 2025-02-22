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
        # Convert action to lowercase for case-insensitive comparison
        action = action.lower()
        
        # Check against values
        for value_name, value_details in self.values.items():
            if isinstance(value_details, dict):
                # If value has detailed structure
                if 'prohibited_actions' in value_details:
                    if any(prohibited.lower() in action for prohibited in value_details['prohibited_actions']):
                        return False
                if 'aligned_actions' in value_details:
                    if any(aligned.lower() in action for aligned in value_details['aligned_actions']):
                        return True
            elif isinstance(value_details, (str, list)):
                # If value is a simple string or list
                values_list = [value_details] if isinstance(value_details, str) else value_details
                if any(value.lower() in action for value in values_list):
                    return True
        
        # Check against personality traits
        for trait, level in self.core_traits.items():
            if isinstance(level, (int, float)):
                # For numeric trait levels (e.g., openness: 0.8)
                if trait.lower() in action:
                    return level > 0.5  # Consider trait aligned if above middle value
        
        # Default to neutral (True) if no specific conflicts found
        return True 