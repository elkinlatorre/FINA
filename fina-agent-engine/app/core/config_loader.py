import yaml
import os
from pathlib import Path
from app.core.logger import get_logger

logger = get_logger("CONFIG_LOADER")


class PromptLoader:
    def __init__(self):
        # Project root folder ('app')
        self.base_dir = Path(__file__).resolve().parents[2]
        self.config_path = self.base_dir / "app" / "prompts" / "system_prompt.yaml"
        logger.info(f"Attempting to load prompt from: {self.config_path}")
        self.prompts = self._load_yaml()

    def _load_yaml(self):
        if not self.config_path.exists():
            logger.error(f"Config file not found at: {self.config_path}")
            if self.config_path.parent.exists():
                logger.info(f"Directory exists. Contents: {os.listdir(self.config_path.parent)}")
            else:
                logger.error(f"Directory {self.config_path.parent} does not exist.")

            raise FileNotFoundError(f"Missing system_prompt.yaml at {self.config_path}")

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error parsing YAML: {str(e)}")
            raise

    def get_analyst_prompt(self) -> str:
        """Constructs the system prompt string from the YAML structure."""
        data = self.prompts.get("financial_analyst", {})

        if not data:
            logger.warning("No 'financial_analyst' key found in YAML.")
            return "You are a professional financial assistant."

        instructions = "\n".join([f"- {i}" for i in data.get("instructions", [])])
        constraints = "\n".join([f"- {c}" for c in data.get("constraints", [])])

        prompt = (
            f"Role: {data.get('role')}\n"
            f"Goal: {data.get('goal')}\n"
            f"Personality: {data.get('personality')}\n\n"
            f"Strict Instructions:\n{instructions}\n\n"
            f"Constraints & Security:\n{constraints}"
        )
        return prompt

# Singleton instance
prompt_loader = PromptLoader()