from pydantic_ai import Agent, RunContext
import os
from dataclasses import dataclass
from typing import Union
from .model import get_model
from .calendar_availability import SelectedAppointment
from .set_meeting_details import MeetingDetails
import dotenv
import asyncio
dotenv.load_dotenv()

system_prompt= """
Role: Contact Information Gatherer
Task: The user has already gave the details for their appointment. Collect user contact details for appointment scheduling, then confirm the booking.

Gather the following:
1. Full Name (required)
2. Email Address (required, validate format)
3. Phone Number (optional)

Behavior:
- Go Straight with a brief, friendly request for the missing details only.
- Keep messages concise.
- Do not ask for timezone.
- Ask the user for the data missing.

Tool usage:
- When (and only when) you have both Full Name and a valid Email, call the tool: set_event.
- Call set_event exactly once.
- After the tool returns:
  - If successful, confirm the booking and include any link returned by the tool.
  - If it returns an error message, briefly apologize and ask the user to correct the missing/invalid info.

Output:
- Return the required data
"""

model = get_model()

gather_contact_information_agent = Agent[None, SelectedAppointment](
    model=model,
    system_prompt=system_prompt,
    output_type=[str,MeetingDetails]
)

@dataclass
class ContactInformation:
    """Model to hold user contact information."""
    full_name: str
    email: str
    phone_number: Union[str, None]


async def main():
    user_input = "my name is wonder and my email is criptowder@gmail.com\n\nmy phone number is +573224845533"
    selected_appointment = SelectedAppointment(id='3pvnq212mnaom093nn9rpoe0oc')
    message_history = []

    run = await gather_contact_information_agent.run(
        user_prompt="",
        deps=selected_appointment,
        message_history=message_history
    )

    print(run.output)

if __name__ == "__main__":  
    asyncio.run(main())
