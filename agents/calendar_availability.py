import os
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext

@dataclass
class DesiredAppointment:
    date: str
    time: str

from .utils import get_model
import dotenv
from utils.google_calendar_manager import GoogleCalendarManager

dotenv.load_dotenv()

model = get_model()
# Look for alternatives to show the appointment confirmation
prompt = """
Role: Intelligent Calendar Availability Assistant
Task: Help users find/book available time slots by:

Checking their calendar for the specified date/time (using get_calendar_tool).

Availability Rule: Only slots with an event explicitly named "Available" are considered open. If none exist, return "Unavailable".

Present valid slots to the user.

User Options:

Request a different day/time.

On Confirmation: Return the chosen slot in the desired output format.

Output: Always adhere to the specified formatting rules.
"""



calendar_availability_agent = Agent(model=model, system_prompt=prompt)

calendar_manager = GoogleCalendarManager(
        service_account_file='./client_secrets.json',
        calendar_id=os.getenv("CALENDAR_ID", "primary")
        
    )


@calendar_availability_agent.tool
async def get_calendar_tool(ctx: RunContext[None], date: str, time: str) -> str:
    """
    Get calendar events for a specific date and time.
    
    """
    # Placeholder for actual calendar fetching logic
    return f"Checking calendar for events on {date} at {time}."


@calendar_availability_agent.tool
async def choose_available_slot_tool(ctx: RunContext[None], date: str, time: str) -> str:
    """
    Suggest the next available time slot if the desired slot is not available.
    
    """

    events = calendar_manager.get_events(max_results=5)

    print(events)
    # Placeholder for actual logic to find the next available slot
    return events
