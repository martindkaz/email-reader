"""Configuration for LangGraph Agent"""

import os
from dotenv import load_dotenv

load_dotenv()

# Anthropic API Configuration
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
if not ANTHROPIC_API_KEY:
    raise ValueError(
        "ANTHROPIC_API_KEY not found in environment variables. "
        "Please add it to your .env file"
    )

# Claude Model Configuration
CLAUDE_MODEL = "claude-sonnet-4-20250514"  # Claude Sonnet 4.5

# Agent Configuration
AGENT_MAX_ITERATIONS = 10
AGENT_VERBOSE = True
