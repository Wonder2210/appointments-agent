from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.config import get_stream_writer
from langgraph.types import interrupt
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from pydantic_graph import End
from typing_extensions import TypedDict
from typing import Dict, List, Annotated
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter, PartDeltaEvent, PartStartEvent, ToolCallPartDelta, ToolCallPart

from agents.gather_information import gather_information_agent, DesiredAppointment
from agents.calendar_availability import calendar_availability_agent
from agents.gather_contact_information import gather_contact_information_agent

import asyncio

class State(TypedDict):
    messages: Annotated[List[bytes], lambda x, y: x + y]
    contact_information: Dict[str, str]
    selected_appointment: Dict[str, str]
    user_input: str
    user_requirements: DesiredAppointment

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
    user_input = state["user_input"]

    writer = get_stream_writer()

    data: Dict[str, str] = {}

    print(f"Gathering information for user input: {user_input}")

    message_history: list[ModelMessage] = []
    for message_row in state['messages']:
        message_history.extend(ModelMessagesTypeAdapter.validate_json(message_row))

    async with gather_information_agent.iter(user_input, message_history=message_history) as run:
        async for node in run:
            if isinstance(node, End):
                data = node.data.output
                break
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
    print(f"Checking calendar availability for: {user_input}")

    writer = get_stream_writer()

    data = {}

    message_history: list[ModelMessage] = []
    for message_row in state['messages']:
        message_history.extend(ModelMessagesTypeAdapter.validate_json(message_row))

    print("Checking calendar availability with user requirements:", user_requirement)

    async with calendar_availability_agent.iter(user_prompt=user_input,deps=user_requirement, message_history=message_history) as run:
        async for node in run:
            if isinstance(node, End):
                if not isinstance(node.data.output, DesiredAppointment):
                    continue
                else:
                    data = node.data.output
            elif Agent.is_model_request_node(node):
                async with node.stream(run.ctx) as request_stream:
                    await process_stream(request_stream, writer)

    if data:
        return {
            "selected_appointment": data,
            "messages": [run.result.new_messages_json()]
        }

async def gather_contact_information_node(state: State) -> Dict[str, str]:
    """
    Node to gather contact information from the user.
    """
    contact_info = state["contact_information"]
    print(f"Gathering contact information: {contact_info}")


    writer = get_stream_writer()

    data = {}

    message_history: list[ModelMessage] = []
    for message_row in state['messages']:
        message_history.extend(ModelMessagesTypeAdapter.validate_json(message_row))

    async with gather_contact_information_agent.iter(contact_info, message_history=message_history) as run:
        async for node in run:
            if isinstance(node, End):
                data = node.data.output
            elif Agent.is_model_request_node(node):
                async with node.stream(run.ctx) as request_stream:
                    await process_stream(request_stream, writer)

    return {
        "contact_information": data,
        "messages": [run.result.new_messages_json()]
    }

def no_time_selected_router(state: State) -> str:
    """
    Route the state to the appropriate node based on whether a time was selected.
    """
    desired_appt = state.get("user_requirements", {})

    if not isinstance(desired_appt, DesiredAppointment):
        return "wait_message"
    elif isinstance(desired_appt, DesiredAppointment):
        return "calendar_availability"

def non_selected_appt_router (state: State) -> str:
    """
    Route the state to the appropriate node based on the current step.
    """
    desired_appt = state.get("selected_appointment", None)
    print(f"Routing based on selected appointment: {desired_appt}")

    if not desired_appt:
        return "wait_message"
    elif isinstance(desired_appt, str):
        print("No appointment selected, waiting for user input.")
        return "wait_calendar_availability"
    elif isinstance(desired_appt, DesiredAppointment):
        print("Appointment selected, gathering contact information.")
        return "gather_contact_information"
    return "wait_calendar_availability"

def get_next_user_message(state: State):
    value = interrupt("")

    # Set the user's latest message for the LLM to continue the conversation
    return {
        "user_input": value
    }    


def build_graph():
    """
    Build the graph with the gather_info_node and calendar_availability_node.
    """

    graph_builder = StateGraph(State)
    graph_builder.add_node("wait_message", get_next_user_message)
    graph_builder.add_node(
        "gather_information",
        gather_info_node,
    )
    
    graph_builder.add_node(
        "calendar_availability",
        calendar_availability_node,
    )

    graph_builder.add_node(
        "gather_contact_information",
        gather_contact_information_node,
    )

    graph_builder.add_node("wait_calendar_availability", get_next_user_message)

    graph_builder.add_edge(START, "gather_information")

    graph_builder.add_conditional_edges("gather_information", no_time_selected_router, ["wait_message", "calendar_availability"])
    graph_builder.add_edge("wait_message", "gather_information")

    graph_builder.add_conditional_edges("calendar_availability", non_selected_appt_router, ["wait_calendar_availability", "wait_message", "gather_contact_information", "gather_information"])

    graph_builder.add_edge("wait_calendar_availability", "calendar_availability")
    graph_builder.add_edge("calendar_availability", "gather_contact_information")
    graph_builder.add_edge(
        "gather_contact_information",
        END,
    )
    memory = MemorySaver()

    return graph_builder.compile(checkpointer=memory)

graph = build_graph()

async def run_agent(usr_input: str):
    initial_state = {
        "messages": [],
        "user_input": usr_input,
        "user_requirements": {},
        "contact_information": {},
        "selected_appointment": {}
    }


    async for chunk in graph.astream(initial_state, stream_mode="custom"):
        yield chunk


async def main():
   print(graph.get_graph().draw_mermaid())
    # user_input = "I would like to schedule an appointment"

    # res = ""

    # async for message in run_agent(user_input):
    #   res += message
    #   print(res)


if __name__ == "__main__":
    asyncio.run(main())