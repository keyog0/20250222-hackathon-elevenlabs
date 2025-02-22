import json
import os
from typing import Dict, Any, Optional
from pydantic import BaseModel


class Config(BaseModel):
    """Configuration model for the agent."""

    openai_api_key: str
    model_name: str = "gpt-4o-mini"
    data_dir: str = "data"

    # Optional configurations
    max_history_length: int = 50
    memory_significance_threshold: float = 0.5
    temperature: float = 0.7
    max_tokens: int = 1000


class ConfigManager:
    """Manages configuration and data loading for the agent."""

    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config: Optional[Config] = None

    def load_config(self) -> Config:
        """Load configuration from file or environment variables."""
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                config_data = json.load(f)
        else:
            # Fall back to environment variables
            config_data = {
                "openai_api_key": os.getenv("OPENAI_API_KEY"),
                "model_name": os.getenv("MODEL_NAME", "gpt-4o-mini"),
                "data_dir": os.getenv("DATA_DIR", "data"),
            }

        if not config_data.get("openai_api_key"):
            raise ValueError("OpenAI API key not found in config or environment variables")

        self.config = Config(**config_data)
        return self.config

    def load_persona(self, persona_id: str) -> Dict[str, Any]:
        """Load persona data from JSON file."""
        if not self.config:
            raise RuntimeError("Config not loaded. Call load_config() first.")

        persona_path = os.path.join(self.config.data_dir, "personas", f"{persona_id}.json")

        if not os.path.exists(persona_path):
            raise FileNotFoundError(f"Persona file not found: {persona_path}")

        with open(persona_path, "r") as f:
            return json.load(f)

    def load_scenario(self, scenario_id: str) -> Dict[str, Any]:
        """Load scenario data from JSON file."""
        if not self.config:
            raise RuntimeError("Config not loaded. Call load_config() first.")

        scenario_path = os.path.join(self.config.data_dir, "scenarios", f"{scenario_id}.json")

        if not os.path.exists(scenario_path):
            raise FileNotFoundError(f"Scenario file not found: {scenario_path}")

        with open(scenario_path, "r") as f:
            return json.load(f)

    def load_all_scenarios(self) -> Dict[str, Dict[str, Any]]:
        """Load all available scenarios."""
        if not self.config:
            raise RuntimeError("Config not loaded. Call load_config() first.")

        scenarios_dir = os.path.join(self.config.data_dir, "scenarios")
        scenarios = {}

        if not os.path.exists(scenarios_dir):
            raise FileNotFoundError(f"Scenarios directory not found: {scenarios_dir}")

        for filename in os.listdir(scenarios_dir):
            if filename.endswith(".json"):
                scenario_id = filename[:-5]  # Remove .json extension
                scenarios[scenario_id] = self.load_scenario(scenario_id)

        return scenarios

    def ensure_data_directories(self):
        """Ensure required data directories exist."""
        if not self.config:
            raise RuntimeError("Config not loaded. Call load_config() first.")

        os.makedirs(os.path.join(self.config.data_dir, "personas"), exist_ok=True)
        os.makedirs(os.path.join(self.config.data_dir, "scenarios"), exist_ok=True)
