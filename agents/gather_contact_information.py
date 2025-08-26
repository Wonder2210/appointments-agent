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
Task: Collect user contact details to finish the appointment scheduling

Gather the following:
1. Full Name (required)
2. Email Address (required, validate format)
3. Phone Number (optional)

Behavior:
- Go Straight with a brief, friendly request for the missing details only.
- Keep messages concise.
- Do not ask for timezone.
- Ask the user for the data missing.

Output:
- Return the required data
"""

model = get_model()

async def format_user_info(ctx: RunContext, info) -> MeetingDetails:
    return MeetingDetails(
        full_name=info.get("name", ""),
        email=info.get("email", ""),
        phone_number=info.get("phone", None),
        selected_appointment=ctx.deps
    )

gather_contact_information_agent = Agent(
    model=model,
    system_prompt=system_prompt,
    deps_type=SelectedAppointment,
    output_type=Union[str, MeetingDetails]
)

@dataclass
class ContactInformation:
    """Model to hold user contact information."""
    full_name: str
    email: str
    phone_number: Union[str, None]


async def main():
    user_input = "my name is wonder and my email is test@gmail.com\n\nmy phone number is +123345678"
    selected_appointment = SelectedAppointment(id='3pvnq212mnaom093nn9rpoe0oc')
    message_history = []

    run = await gather_contact_information_agent.run(
        user_prompt=user_input,
        deps=selected_appointment,
        message_history=message_history
    )

    print(run.output)

if __name__ == "__main__":  
    asyncio.run(main())
