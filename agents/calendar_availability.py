import os
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext, TextOutput

import logfire

from .model import get_model
import dotenv
from .google_calendar_manager import GoogleCalendarManager
from datetime import datetime, date, time

dotenv.load_dotenv()
logfire.configure(token=os.getenv("LOGFIRE_API_KEY"))
logfire.instrument_pydantic_ai()

@dataclass
class DesiredAppointment:
    min_date: str
    max_date: str
    time: str

@dataclass
class SelectedAppointment:
    id: str

@dataclass
class NoAvailableSlots:
    message: str

model = get_model()
# Look for alternatives to show the appointment confirmation
prompt = """
Role: Intelligent Calendar Availability Assistant
Task: Help users find/book available time slots by:

Checking Calendar Availability:

Use the get_calendar_tool to retrieve events for the specified date/time range.

Availability Rule: Only time slots with an event explicitly named "Available" are considered open. If none exist, return "Unavailable for [date/time]."

User Interaction Flow:

If the user provides a specific date/time, check for availability and:

If available, confirm booking (a simple "yes" suffices).

If unavailable, suggest: "No slots open at [date/time]. Would you like to check another time or list available slots?"

If the user asks to "list available slots" (or similar phrasing), use get_calendar_tool to scan their calendar and return all slots marked "Available" for the specified day/time range.

Output: Return the id of the selected appointment or a message indicating unavailability with the date and time.
"""

calendar_availability_agent = Agent[DesiredAppointment, None](model=model, system_prompt=prompt, output_type=[str, SelectedAppointment, NoAvailableSlots])

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

@calendar_availability_agent.tool
async def get_availability_tool(ctx: RunContext[None], date: str, time: str) -> str:
    """
    Display all the next available spots
    
    """
    print(f"Checking availability for {date} at {time}")

    events = calendar_manager.get_events(max_results=5)

    # logfire.info(f"Found events: {events}")
    # Placeholder for actual logic to find the next available slot
    return events


async def run():
    """
    Main function to run the calendar availability agent.
    """
    user_input = "list all available spots for next week"

    # Run the agent with the user input
    response = await calendar_availability_agent.run(
        user_input=user_input,
        deps=DesiredAppointment(
            min_date=date(2025, 8, 17),
            max_date=date(2025, 8, 23),
            time=time(10, 0)
        )
    )

    if response is not None:
        if isinstance(response.output, SelectedAppointment):
            print(f"Selected Appointment ID: {response.output.id}")
        else:
            print(response.output)
    else:
        print("Failed to gather the necessary information from the user.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(run())
