import os
from typing import Union
from pydantic_ai import Agent, RunContext
from dataclasses import dataclass
from .model import get_model
from .google_calendar_manager import GoogleCalendarManager
from .calendar_availability import SelectedAppointment

model = get_model()

@dataclass
class MeetingDetails:
    full_name: str
    email: str
    phone_number: Union[str, None]
    selected_appointment: SelectedAppointment

prompt = """
Role: Meeting Details Setter
Task: Set meeting details for the selected appointment calling the set_event tool.

"""

set_meeting_details_agent = Agent[MeetingDetails, str](
    model=model,
    system_prompt=prompt,
    deps_type=MeetingDetails,
    output_type=str
)

@set_meeting_details_agent.tool
def set_event(ctx: RunContext[MeetingDetails]) -> str:
    """
    Create/update the calendar event for the selected appointment with the provided contact info.
    Returns a short confirmation message with a link when available, or an error message if something fails.
    """
    # Get meeting details from context
    meeting_details = ctx.deps
    if not isinstance(meeting_details, MeetingDetails) or not meeting_details.full_name or not meeting_details.email:
        return "Error: Missing required meeting information"
    
    # Initialize calendar manager
    calendar_manager = GoogleCalendarManager(
        service_account_file='./client_secrets.json',
        calendar_id=os.getenv("CALENDAR_ID", "primary")
    )
    
    # Create event description with contact info
    description = f"Meeting with {meeting_details.full_name}\nEmail: {meeting_details.email}"
    if meeting_details.phone_number:
        description += f"\nPhone: {meeting_details.phone_number}"
    
    # Create calendar event (simplified - would need proper datetime parsing in real usage)
    try:
        event = calendar_manager.update_event(
            event_id=meeting_details.selected_appointment.id,
            title=f"Meeting with {meeting_details.full_name}",
            description=description,
            location="Online"
        )
        print(event)
        link = event.get("link") or event.get("htmlLink") or ""
        if link:
            return f"Event created successfully: {link}"
        return "Event created successfully."
    except Exception as e:
        return f"Failed to create event: {str(e)}"
