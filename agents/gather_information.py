from typing import Union
from datetime import date, time

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.deepseek import DeepSeekProvider
from rich.prompt import Prompt
from utils import get_model


model = get_model()

prompt = """
You are a calendar availability agent, and your task to help users find available time slots in their calendar is gather the necessary information from the user.
You will ask the user for the date and time they want to check for available slots.

Output all in the desired format
"""

class DesiredAppointment(BaseModel):
    """Desired date and time for the appointment."""
    date: date
    time: time

class Failed(BaseModel):
    """Unable to gather the necessary information from the user."""

gather_information_agent = Agent(model=model, result_type=Union[DesiredAppointment, Failed], system_prompt=prompt)


async def main():
        # Simulate user input
        user_input = Prompt.ask("Hi which date and time do you want to check for available slots? (e.g., 2023-10-15 at 10:00 AM)")
        response = await gather_information_agent.run(user_input)
        if response is not None:
            if isinstance(response.output, DesiredAppointment):
                print(f"Desired Appointment: {response.output}")
            else:
                print("Failed to gather the necessary information from the user.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
