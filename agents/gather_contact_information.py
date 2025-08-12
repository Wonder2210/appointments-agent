from pydantic_ai import Agent, RunContext
import os
from dataclasses import dataclass
from typing import Union
from datetime import datetime, timedelta
from .model import get_model
from .calendar_availability import DesiredAppointment
from agents.google_calendar_manager import GoogleCalendarManager
import dotenv
dotenv.load_dotenv()

system_prompt= """
Role: Contact Information Gatherer
Task: Collect user contact details for appointment scheduling.
Start with a friendly greeting and ask for the user's contact information, for the meeting.
Gather the following information:
1. Full Name (required)
2. Email Address (required)
3. Phone Number (optional)
Rules:
- Ensure all required fields are provided.
- Validate email format.
- Phone number is optional but should be collected if available.
Output: Return in the following order the contact information:
1. Full Name
2. Email Address
3. Phone Number (if provided)
"""

model = get_model()

@dataclass
class ContactInformation:
    """Model to hold user contact information."""
    full_name: str
    email: str
    phone_number: Union[str, None]

def set_event(ctx: RunContext[None], full_name: str, email: str, phone_number: Union[str, None]) -> str:
    """
    Set the contact information for the user and create calendar event.
    """
    # Get appointment time from context
    desired_appt = ctx.deps
    if not isinstance(desired_appt, DesiredAppointment):
        return "Error: Missing appointment time information"
    
    # Initialize calendar manager
    calendar_manager = GoogleCalendarManager(
        service_account_file='./client_secrets.json',
        calendar_id=os.getenv("CALENDAR_ID", "primary")
    )
    
    # Create event description with contact info
    description = f"Meeting with {full_name}\nEmail: {email}"
    if phone_number:
        description += f"\nPhone: {phone_number}"
    
    # Create calendar event (simplified - would need proper datetime parsing in real usage)
    try:
        event = calendar_manager.update_event(
            event_id=desired_appt.id,
            title=f"Meeting with {full_name}",
            start_time=datetime.strptime(f"{desired_appt.date} {desired_appt.time}", "%Y-%m-%d %H:%M"),
            end_time=datetime.strptime(f"{desired_appt.date} {desired_appt.time}", "%Y-%m-%d %H:%M") + timedelta(hours=1),
            description=description,
            location="Online"
        )
        return f"Event created successfully: {event['link']}"
    except Exception as e:
        return f"Failed to create event: {str(e)}"


gather_contact_information_agent = Agent[None, DesiredAppointment](
    model=model,
    system_prompt=system_prompt,
    output_type=[set_event, str]
)
