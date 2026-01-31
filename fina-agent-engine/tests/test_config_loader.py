import pytest
import os
from unittest.mock import patch, MagicMock
from app.core.config_loader import PromptLoader

def test_prompt_loader_file_not_found():
    with patch("pathlib.Path.exists", return_value=False):
        with pytest.raises(FileNotFoundError):
            PromptLoader()

def test_prompt_loader_get_analyst_prompt_fallback():
    # Mocking yaml content to be empty
    with patch("builtins.open", MagicMock()):
        with patch("yaml.safe_load", return_value={}):
            loader = PromptLoader()
            prompt = loader.get_analyst_prompt()
            assert "professional financial assistant" in prompt

def test_prompt_loader_get_analyst_prompt_success():
    mock_yaml = {
        "financial_analyst": {
            "role": "Analyst",
            "goal": "Help",
            "personality": "Nice",
            "instructions": ["Do things"],
            "constraints": ["Safe"]
        }
    }
    with patch("builtins.open", MagicMock()):
        with patch("yaml.safe_load", return_value=mock_yaml):
            loader = PromptLoader()
            prompt = loader.get_analyst_prompt()
            assert "Role: Analyst" in prompt
            assert "Do things" in prompt
