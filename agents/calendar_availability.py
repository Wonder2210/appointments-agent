import asyncio
from httpx import AsyncClient

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.deepseek import DeepSeekProvider
from utils import get_model


model = get_model()

prompt = """
Given the date and time, get the events using the 'get_calendar_tool' that might fit with the requirements of the user. If there are no events.
"""

calendar_availability_agent = Agent(model=model, system_prompt=prompt)


@calendar_availability_agent.tool
async def get_calendar_tool(date: str, time: str) -> str:
    """
    Get calendar events for a specific date and time.
    
    """
    # Placeholder for actual calendar fetching logic
    return f"Checking calendar for events on {date} at {time}."

async def main():
    async with RunContext(calendar_availability_agent) as context:
        # Simulate user input
        user_input = "I want to check my calendar for events on 2023-10-15 at 10:00 AM."
        response = await context.run(user_input)
        print(response)
if __name__ == "__main__":
    asyncio.run(main())
