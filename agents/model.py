
from pydantic_ai.models.anthropic import AnthropicModel
from dotenv import load_dotenv
import os

load_dotenv()

def get_model():
    return AnthropicModel('claude-3-7-sonnet-latest')
