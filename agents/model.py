from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIModel
from dotenv import load_dotenv
import os

load_dotenv()


def get_model():
    return OpenAIModel(
    "gpt-4o",
    provider=OpenAIProvider(
        api_key=os.getenv("OPENAI_API_KEY"),
    ),
)