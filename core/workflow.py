from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition
from core.state import AgentState
from core.model import model_with_tools
from tools import tools

def call_model(state: AgentState):
    messages = state["messages"]
    response = model_with_tools.invoke(messages)
    return {"messages": [response]}

def build_workflow():
    wf = StateGraph(AgentState)
    tool_node = ToolNode(tools)
    
    wf.add_node("agent", call_model)
    wf.add_node("tools", tool_node)
    
    wf.add_edge(START, "agent")
    wf.add_conditional_edges("agent", tools_condition)
    wf.add_edge("tools", "agent")
    
    return wf.compile()
