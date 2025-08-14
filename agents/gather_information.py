from typing import Union
from datetime import date, time

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.providers.deepseek import DeepSeekProvider
from rich.prompt import Prompt
from .model import get_model
from datetime import datetime



model = get_model()

prompt = """
Role: Calendar Availability Agent
Task: Help users look for open time slots by gathering:

Date (required, e.g., "June 10", "tomorrow"—must be today or future).

Time (optional; defaults to current time if omitted).

Rules:

Use the 'current_date_and_time' tool for relative inputs (e.g., "next week").

if users ask for the next week retrive the next week starting at sunday.

Reject past dates—prompt for a valid future date.

Reject whole months requests

Format responses clearly for usability.
"""

class DesiredAppointment(BaseModel):
    """Desired date and time for the appointment."""
    min_date: date
    max_date: date
    time: time

class Failed(BaseModel):
    """Unable to gather the necessary information from the user."""

gather_information_agent = Agent(model=model, result_type=Union[DesiredAppointment, Failed, str], system_prompt=prompt)

@gather_information_agent.tool
async def current_date_and_time(ctx: RunContext[None]) -> datetime:
    """
    Get the current date and time.
    """
    now = datetime.now()
    return now


async def main():
        # Simulate user input
        user_input = Prompt.ask("Hi which date and time do you want to check for available slots? (e.g., 2023-10-15 at 10:00 AM)")
        response = await gather_information_agent.run(user_input)
        if response is not None:
            if isinstance(response.output, DesiredAppointment):
                print(f"Desired Appointment: {response.output}")
            else:
                # print(response.all_messages())
                print("Failed to gather the necessary information from the user.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())