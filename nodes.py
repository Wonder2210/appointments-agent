
from typing import Annotated, Dict, List, TypedDict, Literal
from pydantic_ai import Agent
from pydantic_graph import End
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter, PartDeltaEvent, PartStartEvent, ToolCallPartDelta, ToolCallPart
from langgraph.config import get_stream_writer
from langgraph.types import interrupt, Command
from agents.gather_information import gather_information_agent, DesiredAppointment
from agents.calendar_availability import calendar_availability_agent, SelectedAppointment
from agents.gather_contact_information import gather_contact_information_agent
from agents.set_meeting_details import set_meeting_details_agent, MeetingDetails

class State(TypedDict):
    messages: Annotated[List[bytes], lambda x, y: x + y]
    contact_information: Dict[str, str]
    selected_appointment: Dict[str, str]
    user_input: str
    user_requirements: DesiredAppointment
    meeting_details: MeetingDetails

async def handle_event(event, writer):
    """
    Handle a single event and write its content if applicable.
    """
    if isinstance(event, PartStartEvent) and not isinstance(event.part, ToolCallPart):
        if event.part.content:
            writer(event.part.content)
    elif isinstance(event, PartDeltaEvent) and not isinstance(event.delta, ToolCallPartDelta):
        if event.delta.content_delta:
            writer(event.delta.content_delta)


async def process_stream(request_stream, writer):
    """
    Process the stream of events and delegate handling to `handle_event`.
    """
    async for event in request_stream:
        await handle_event(event, writer)

async def gather_info_node(state: State,) -> Dict[str, str]:
    """
    Node to gather information from the user.
    """
    user_input = state.get("user_input", "")

    writer = get_stream_writer()

    data: Dict[str, str] = {}

    message_history: list[ModelMessage] = []
    for message_row in state['messages']:
        message_history.extend(ModelMessagesTypeAdapter.validate_json(message_row))

    async with gather_information_agent.iter(user_input, message_history=message_history) as run:
        async for node in run:
            if isinstance(node, End):
                data = node.data.output
            elif Agent.is_model_request_node(node):
                async with node.stream(run.ctx) as request_stream:
                    await process_stream(request_stream, writer)

    return {
        "user_requirements": data,
        "messages": [run.result.new_messages_json()]
    }

async def calendar_availability_node(state: State) -> Dict[str, str]:
    """
    Node to check calendar availability and book appointments.
    """
    user_requirement = state["user_requirements"]
    user_input = state["user_input"]

    data = None

    message_history: list[ModelMessage] = []
    for message_row in state['messages']:
        message_history.extend(ModelMessagesTypeAdapter.validate_json(message_row))

    async with calendar_availability_agent.iter(user_prompt=user_input,deps=user_requirement, message_history=message_history) as run:
        async for node in run:
            if isinstance(node, End):
                if isinstance(node.data.output, SelectedAppointment):
                    data = node.data.output
    return {
            "selected_appointment": data,
            "messages": [run.result.new_messages_json()]
        }

async def gather_contact_information_node(state: State) -> Dict[str, str]:
    """
    Node to gather contact information from the user.
    """
    selected_appointment = state["selected_appointment"]
    user_input = state["user_input"]


    writer = get_stream_writer()

    data = {}

    message_history: list[ModelMessage] = []
    for message_row in state['messages']:
        message_history.extend(ModelMessagesTypeAdapter.validate_json(message_row))

    run = await gather_contact_information_agent.run(
        user_prompt=user_input,
        deps=selected_appointment,
        message_history=message_history
    )

    if not isinstance(run.output, MeetingDetails):
        print(run.output)
        writer(run.output)

    data = run.output if isinstance(run.output, MeetingDetails) else False

    return {
        "meeting_details": data,
        "messages": [run.all_messages_json()]
    }

async def set_meeting_details_node(state: State) -> Dict[str, str]:
    """
    Node to set the meeting details.
    """
    meeting_details = state["meeting_details"]

    writer = get_stream_writer()

    
    message_history: list[ModelMessage] = []
    for message_row in state['messages']:
        message_history.extend(ModelMessagesTypeAdapter.validate_json(message_row))

    result = await set_meeting_details_agent.run(deps=meeting_details, message_history=message_history)

    writer(result.output)

    return {
        "messages": [result.all_messages_json()]
    }

def verify_user_date_node(state: State):
    """
    Node to verify the user's desired date and time.
    """
    user_requirements = state["user_requirements"]

    if isinstance(user_requirements, DesiredAppointment):
        return "calendar_availability"
    return "wait_message"

def non_selected_appt_router (state: State) -> str:
    """
    Route the state to the appropriate node based on the current step.
    """
    desired_appt = state.get("selected_appointment", None)

    if isinstance(desired_appt, SelectedAppointment):
        return "gather_contact_information"
    return "wait_for_another_time"

def get_next_user_message(state: State):
    value = interrupt("")

    # Set the user's latest message for the LLM to continue the conversation
    return {
        "user_input": value
    }

def ask_user_for_another_time(state: State) -> Command[Literal["wait_message"]]:
    """
    Ask the user for another time if the selected time is not available.
    """
    return Command(goto="wait_message")

def user_data_router(state: State) -> str:
    """
    Route the state to the appropriate node based on whether user data is available.
    """
    user_data = state.get("meeting_details", None)

    if isinstance(user_data, MeetingDetails):
        return "set_meeting_details"
    return "wait_for_user_details" 



def no_time_selected_router(state: State) -> str:
    """
    Route the state to the appropriate node based on whether a time was selected.
    """
    desired_appt = state.get("user_requirements")

    if not isinstance(desired_appt, DesiredAppointment):
        return "wait_message"
    elif isinstance(desired_appt, DesiredAppointment):
        return "calendar_availability"
