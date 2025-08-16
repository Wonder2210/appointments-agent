from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from agents.calendar_availability import SelectedAppointment
from nodes import (
    State,
    ask_user_for_another_time,
    get_next_user_message,
    gather_info_node,
    calendar_availability_node,
    gather_contact_information_node,
    non_selected_appt_router,
    set_meeting_details_node,
    user_data_router,
    verify_user_date_node
)

import asyncio

def build_graph():
    """
    Build the graph with the gather_info_node and calendar_availability_node.
    """

    graph_builder = StateGraph(State)
    graph_builder.add_node(
        "gather_information",
        gather_info_node,
    )

    graph_builder.add_node("verify_user_date", verify_user_date_node)

    graph_builder.add_node(
        "calendar_availability",
        calendar_availability_node,
    )

    graph_builder.add_node(
        "gather_contact_information",
        gather_contact_information_node,
    )

    graph_builder.add_node("wait_message", get_next_user_message)

    graph_builder.add_node(
        "wait_for_user_details",
        get_next_user_message,
    )

    graph_builder.add_node("set_meeting_details", set_meeting_details_node)

    graph_builder.add_node("wait_for_another_time", ask_user_for_another_time)

    graph_builder.add_edge(START, "gather_information")

    graph_builder.add_edge("wait_message", "gather_information")

    graph_builder.add_conditional_edges("gather_information", verify_user_date_node)
    graph_builder.add_conditional_edges("calendar_availability", non_selected_appt_router)
    graph_builder.add_conditional_edges("gather_contact_information", user_data_router)
    graph_builder.add_edge("wait_for_user_details", "gather_contact_information")

    graph_builder.add_edge("gather_contact_information", "set_meeting_details")

    graph_builder.add_edge("set_meeting_details", END)

    memory = MemorySaver()

    return graph_builder.compile(checkpointer=memory)

graph = build_graph()

async def run_agent(usr_input: str):
    initial_state = {
        "messages": [],
        "user_input": usr_input,
        "user_requirements": {},
        "selected_appointment": SelectedAppointment(id='3pvnq212mnaom093nn9rpoe0oc')
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