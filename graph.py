from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.config import get_stream_writer
from pydantic_graph import End
from typing_extensions import TypedDict
from typing import Dict, List, Annotated
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter, PartDeltaEvent, PartStartEvent, ToolCallPartDelta, ToolCallPart
from dataclasses import dataclass

from agents.gather_information import gather_information_agent
from agents.calendar_availability import calendar_availability_agent

import asyncio

class State(TypedDict):
    messages: Annotated[List[bytes], lambda x, y: x + y]
    contact_information: Dict[str, str]
    selected_appointment: Dict[str, str]
    user_input: str

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
        "contact_information": data,
        "messages": [run.result.new_messages_json()]
    }

async def calendar_availability_node(state: State) -> Dict[str, str]:
    """
    Node to check calendar availability and book appointments.
    """
    user_input = state["contact_information"]

    writer = get_stream_writer()

    data = {}

    message_history: list[ModelMessage] = []
    for message_row in state['messages']:
        message_history.extend(ModelMessagesTypeAdapter.validate_json(message_row))

    async with calendar_availability_agent.iter(user_input, message_history=message_history) as run:
        async for node in run:
            if isinstance(node, End):
                data = node.data.output
            elif Agent.is_model_request_node(node):
                async with node.stream(run.ctx) as request_stream:
                    await process_stream(request_stream, writer)

    return {
        "selected_appointment": data,
        "messages": [run.result.new_messages_json()]
    }

def build_graph():
    """
    Build the graph with the gather_info_node and calendar_availability_node.
    """

    graph_builder = StateGraph(State)
    graph_builder.add_node(
        "gather_information",
        gather_info_node,
    )
    
    # graph_builder.add_node(
    #     "calendar_availability",
    #     calendar_availability_node,
    # )

    graph_builder.add_edge(START, "gather_information")
    # graph_builder.add_edge(
    #     "gather_information",
    #     "calendar_availability",
    # )
    graph_builder.add_edge(
        "gather_information",
        END,
    )

    return graph_builder.compile()

graph = build_graph()

async def run_agent(usr_input: str):
    initial_state = {
        "messages": [],
        "user_input": usr_input,
        "contact_information": {},
        "selected_appointment": {}
    }

    async for chunk in graph.astream(initial_state, stream_mode="custom"):
        yield chunk


async def main():
    user_input = "I would like to schedule an appointment"

    res = ""

    async for message in run_agent(user_input):
      res += message
      print(res)


if __name__ == "__main__":
    asyncio.run(main())