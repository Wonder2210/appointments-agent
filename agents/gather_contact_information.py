from pydantic_ai import Agent, RunContext

from dataclasses import dataclass
from typing import Union
from utils import get_model

from calendar_availability import DesiredAppointment

system_prompt= """
Role: Contact Information Gatherer
Task: Collect user contact details for appointment scheduling.
Gather the following information:
1. Full Name (required)
2. Email Address (required)
3. Phone Number (optional)
Rules:
- Ensure all required fields are provided.
- Validate email format.
- Phone number is optional but should be collected if available.
Output: Return a structured response with the collected information.
"""

model = get_model()

@dataclass
class ContactInformation:
    """Model to hold user contact information."""
    full_name: str
    email: str
    phone_number: Union[str, None]

gather_contact_information_agent = Agent[None, DesiredAppointment](
    model=model,
    system_prompt=system_prompt,
    output_type=ContactInformation
)

@gather_contact_information_agent.tool
def send_email_with_appointment_details(ctx: RunContext[ContactInformation]) -> str:
    """
    Send an email with the appointment details.
    """
    contact_info = ctx.input
    # Here you would implement the logic to send an email using contact_info
    return f"Email sent to {contact_info.email} with appointment details."
