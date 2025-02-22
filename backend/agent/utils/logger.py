import logging
import os
from rich.logging import RichHandler
from typing import Any, Dict

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Set up logging with Rich handler and File handler
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="[%X]",
    handlers=[
        RichHandler(rich_tracebacks=True),
        logging.FileHandler("logs/agent.log")
    ]
)

# Create logger
logger = logging.getLogger("agent")

def log_state_update(node_name: str, state_changes: Dict[str, Any]) -> None:
    """Log state changes from a node."""
    logger.info(f"[{node_name}] State Update:")
    for key, value in state_changes.items():
        logger.info(f"  {key}: {value}")

def log_emotion_update(emotions: Dict[str, float]) -> None:
    """Log emotional state changes."""
    logger.info("[Emotions] Current State:")
    for emotion, intensity in emotions.items():
        logger.info(f"  {emotion}: {intensity:.2f}")

def log_memory_update(memory_type: str, content: Any) -> None:
    """Log memory updates."""
    logger.info(f"[Memory] New {memory_type}:")
    logger.info(f"  {content}")

def log_scenario_update(old_scenario: str, new_scenario: str) -> None:
    """Log scenario transitions."""
    logger.info("[Scenario] Transition:")
    logger.info(f"  {old_scenario} -> {new_scenario}")

def log_response(persona_name: str, response: str) -> None:
    """Log agent's response."""
    logger.info(f"[Response] {persona_name}:")
    logger.info(f"  {response}")

def log_error(node_name: str, error: Exception) -> None:
    """Log errors with context."""
    logger.error(f"[{node_name}] Error occurred:")
    logger.exception(error) 