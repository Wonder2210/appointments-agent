import os
from dataclasses import dataclass

from typing import Union

from pydantic_ai import Agent, RunContext

import logfire

from .utils import get_model
import dotenv
from utils.google_calendar_manager import GoogleCalendarManager

dotenv.load_dotenv()
logfire.configure(token='pylf_v1_us_2j9PfwjqVDCZXvwFK0pxY8ktCW3GZch6mFnlsgZnlDgz')
logfire.instrument_pydantic_ai()

@dataclass
class DesiredAppointment:
    date: str
    time: str

@dataclass
class SelectedAppointment:
    id: str

model = get_model()
# Look for alternatives to show the appointment confirmation
prompt = """
Role: Intelligent Calendar Availability Assistant
Task: Help users find/book available time slots by:

Checking their calendar for the specified date/time (using get_calendar_tool).

Availability Rule: Only slots with an event explicitly named "Available" are considered open. If none exist, return "Unavailable".

Present valid slots to the user.

User Options:

If there are no slots available, request the user for a different day/time.

On Confirmation: Return the chosen slot in the desired output format.

A simple yes can be used to confirm the appointment.

Output: Always adhere to the specified formatting rules.
"""


calendar_availability_agent = Agent[DesiredAppointment, None](model=model, system_prompt=prompt, output_type=Union[SelectedAppointment, str])

calendar_manager = GoogleCalendarManager(
        service_account_file='./client_secrets.json',
        calendar_id=os.getenv("CALENDAR_ID", "primary")
        
    )

# Handle pass down the date and time from the user to the calendar manager
@calendar_availability_agent.tool
async def get_calendar_tool(ctx: RunContext[None], date: str, time: str) -> str:
    """
    Suggest the next available time slot if the desired slot is not available.
    
    """

    events = calendar_manager.get_events(max_results=5)

    # logfire.info(f"Found events: {events}")
    # Placeholder for actual logic to find the next available slot
    return events
