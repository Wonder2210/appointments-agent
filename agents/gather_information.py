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

- Date (required, e.g., "June 10", "tomorrow" — must be today or in the future).
- Time (optional; defaults to current time if omitted).

Rules:
- Use the 'current_date_and_time' tool for relative inputs (e.g., "next week").
- If users ask for "next week," always start from Sunday of the following week.
- Reject past dates — politely prompt for a valid future date.
- Reject requests for whole months.
- DO NOT schedule, confirm, or offer assistance. Your role is ONLY to identify and return the requested date and time.
- Do not add phrases like "I will find open slots" or "Is there anything else I can assist with."
- Just let the user know that you will find if the requested time is available once the date and time is correct
"""

class DesiredAppointment(BaseModel):
    """Desired date and time for the appointment."""
    min_date: str
    max_date: str
    time: str

# class Failed(BaseModel):
#     """Unable to gather the necessary information from the user."""

gather_information_agent = Agent(model=model, output_type=Union[str, DesiredAppointment], system_prompt=prompt)

@gather_information_agent.tool
async def current_date_and_time(ctx: RunContext[None]) -> str:
    """
    Get the current date and time.
    """
    now = datetime.now().isoformat()
    return now


async def main():
        # Simulate user input
        user_input = Prompt.ask("Hi which date and time do you want to check for available slots? (e.g., 2023-10-15 at 10:00 AM)")
        response = await gather_information_agent.run(user_input)
        if response is not None:
            if isinstance(response.output, DesiredAppointment):
                print(f"Desired Appointment: {response.output}")
            # elif isinstance(response.output, Failed):
            #     print("Failed to gather the necessary information from the user.")
            # else:
            #     print(f"Unexpected output type: {type(response.output)}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
