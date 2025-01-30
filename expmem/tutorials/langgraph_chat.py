import os

from typing import Annotated, Literal
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI

from langchain_community.tools.tavily_search import TavilySearchResults

from dotenv import load_dotenv
load_dotenv()

tool = TavilySearchResults(max_results=2, tavily_api_key=os.getenv("TAVILY_API_KEY"))
tools = [tool]
res = tool.invoke("What's a 'node' in LangGraph?")

print(res)

class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

llm = ChatOpenAI(model="gpt-4o-mini-2024-07-18", 
                 api_key=os.getenv("OPENAI_API_KEY"),
                 max_tokens=500)

llm_tools = llm.bind_tools(tools)

import json
from langchain_core.messages import ToolMessage

class BasicToolNode:
    """A basic tool node that takes a message and returns a message"""

    def __init__(self, tools: list) -> None:
        self.tool_by_name = {tool.name: tool for tool in tools}

    def __call__(self, inputs: dict):
        if messages := inputs.get("messages", []):
            message = messages[-1]

        else:
            raise ValueError("No messages in inputs")
        
        outputs = []

        for tool_call in message.tool_calls:
            tool_result = self.tool_by_name[tool_call["name"]].invoke(
                tool_call["args"]
            )

            outputs.append(
                ToolMessage(
                    content=json.dumps(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )

        return {"messages": outputs}
    
def route_tools(state: State):
    """Use in the conditional_edge to route to the ToolNode if the last message
        has tool calls. Otherwise, route to the end
    """

    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]

    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools"
    
    return END

def chatbot(state: State):
    return {"messages": [llm_tools.invoke(state["messages"])]}

graph_builder.add_conditional_edges(
    "chatbot",
    route_tools,
    {"tools": "tools", END:END}
)

tool_node = BasicToolNode(tools=[tool])
graph_builder.add_node("tools", tool_node)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")
graph = graph_builder.compile()

def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [("user", user_input)]}):
        for value in event.values():
            print("Assistant:", value["messages"][-1].content)



while True:
    try:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        stream_graph_updates(user_input)
    except:
        # fallback if input() is not available
        user_input = "What do you know about LangGraph?"
        print("User: " + user_input)
        stream_graph_updates(user_input)
        break