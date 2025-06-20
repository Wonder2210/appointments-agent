import asyncio

from agents.calendar_availability import DesiredAppointment, SelectedAppointment, calendar_availability_agent
from rich.prompt import Prompt
from pydantic_ai.messages import ModelMessage

from dataclasses import dataclass


@dataclass
class Deps:
    """Dependencies for the calendar availability agent."""
    desired_date: DesiredAppointment

message_history = []

async def run_agent(prompt: str, messages: list[ModelMessage]):
    """Run the calendar availability agent with a sample input."""


    result = await calendar_availability_agent.run(
        prompt,
        deps=Deps(desired_date=DesiredAppointment(date="2023-06-11", time="11:00 AM")),
        message_history=messages
    )
    return result.output, result.all_messages()

async def run_agent_async(prePrompt: str, messages_list: list[ModelMessage] = None):
    prompt = Prompt.ask(prePrompt)
    result, messages = await run_agent(prompt, messages=messages_list)

    if isinstance(result, SelectedAppointment):
        print(f"Desired Appointment: {result}")
        return result  # Return the result instead of continuing recursion
    else:
        # Add await here and return the result
        return await run_agent_async(result, messages_list=messages)

async def main():
    res = await run_agent_async("I would like to check availability for a meeting on June 11 at 11:00 AM.")
    print(f"Final result: {res}")
      
    #   history_messages = []

    #   async with calendar_availability_agent.run_stream( "I would like to check availability for a meeting on June 11 at 11:00 AM.", message_history=history_messages) as result:
    #     curr_response = ""
    #     # print(result.new_messages())
    #     async for message, last in result.stream_structured(debounce_by=0.01):  

    #         data = message
            

    #         print (f"Message: {message}")

    # console.log(result.usage())


# def prettier_code_blocks():
#     """Make rich code blocks prettier and easier to copy.

#     From https://github.com/samuelcolvin/aicli/blob/v0.8.0/samuelcolvin_aicli.py#L22
#     """

#     class SimpleCodeBlock(CodeBlock):
#         def __rich_console__(
#             self, console: Console, options: ConsoleOptions
#         ) -> RenderResult:
#             code = str(self.text).rstrip()
#             yield Text(self.lexer_name, style='dim')
#             yield Syntax(
#                 code,
#                 self.lexer_name,
#                 theme=self.theme,
#                 background_color='default',
#                 word_wrap=True,
#             )
#             yield Text(f'/{self.lexer_name}', style='dim')

#     Markdown.elements['fence'] = SimpleCodeBlock



if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if str(e) == "This event loop is already running":
            loop = asyncio.get_event_loop()
            loop.run_until_complete(main())
        else:
            raise

# Fix prompt to get the chosen appointment
# Instruct the agent how to read the fact that if there is no existing events with the name "Available" in the desired date it should be considered as unavailable