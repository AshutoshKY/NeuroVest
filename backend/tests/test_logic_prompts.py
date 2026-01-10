import pytest
from app.llm_integration.prompts import SYSTEM_PROMPT_V3_PROBABILISTIC, BANNED_WORDS

def test_banned_words_list():
    """Ensure banned words include compliance terms"""
    assert "guarantee" in BANNED_WORDS
    assert "buy now" in BANNED_WORDS
    assert len(BANNED_WORDS) > 10

def test_prompt_no_advice():
    """Ensure prompt explicitly forbids advice"""
    assert "NEVER use advisory language" in SYSTEM_PROMPT_V3_PROBABILISTIC
    assert "purchase" not in SYSTEM_PROMPT_V3_PROBABILISTIC.lower() # Should not be in prompt text instructions as a DO
