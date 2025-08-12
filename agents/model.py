from httpx import AsyncClient
from pydantic_ai.providers.deepseek import DeepSeekProvider
from pydantic_ai.models.openai import OpenAIModel
from dotenv import load_dotenv
import os

load_dotenv()

custom_http_client = AsyncClient(timeout=38)


def get_model():
    return OpenAIModel(
    "deepseek-chat",
    provider=DeepSeekProvider(
        api_key= os.getenv("DEEPSEEK_API_KEY", ""),
        http_client=custom_http_client,
    ),
)