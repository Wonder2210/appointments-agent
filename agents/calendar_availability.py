import os
from dataclasses import dataclass
import json
from pydantic_ai import Agent, RunContext, TextOutput

import logfire

from .model import get_model
import dotenv
from .google_calendar_manager import GoogleCalendarManager, GoogleEvent
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

Objective: Strictly help users find/book available time slots based ONLY on events explicitly named "Available."

Tools: 
- Use get_calendar_tool to retrieve events for the specified date/time range.

Availability Rule:
- A time slot is considered open ONLY if there is an event with the exact title "Available" at that date/time.
- Do NOT infer availability from a lack of events. If no exact match is found, treat it as unavailable.

User Interaction Flow:
1. If the user provides a specific date/time:
   - Query get_calendar_tool for events in that time range.
   - If an event titled exactly "Available" exists at the requested time:
       → Respond with: "Yes" and return the id of that event.
   - If not:
       → Respond: "No slots open at [date/time]. Would you like to check another time or list available slots?"
       → Return None.

2. If the user requests to "list available slots" (or similar):
   - Use get_calendar_tool to find all events titled exactly "Available" within the given date/time range.
   - Return a clear list of available slots with their IDs.

3. If the appointment is found proceed and return the appointment details in the required format output.
"""

calendar_availability_agent = Agent[DesiredAppointment, None](model=model, system_prompt=prompt, output_type=[SelectedAppointment])

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
    return json.dumps(events, indent=2)

@calendar_availability_agent.tool
async def get_availability_tool(ctx: RunContext[None], date: str, time: str) -> str:
    """
    Display all the next available spots, if exist some
    
    """
    print(f"Checking availability for {date} at {time}")

    events = calendar_manager.get_events(max_results=5)
    print (f"Found events: {events}")

    # logfire.info(f"Found events: {events}")
    # Placeholder for actual logic to find the next available slot
    return json.dumps(events, indent=2)


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
