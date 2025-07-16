from pydantic_ai import Agent, RunContext

from dataclasses import dataclass
from typing import Union
from .utils import get_model

from .calendar_availability import DesiredAppointment

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
    Set the contact information for the user.
    """
    print(full_name, ctx.deps)
    return ContactInformation(full_name=full_name, email=email, phone_number=phone_number)


gather_contact_information_agent = Agent[None, DesiredAppointment](
    model=model,
    system_prompt=system_prompt,
    output_type=[set_event, str]
)
