import json
import re
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition
from core.state import AgentState
from core.model import model_with_tools
from tools import tools
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

def sanitize_messages_for_sarvam(messages):
    """
    Sarvam AI (sarvam-m) through its OpenAI-compatible API is strict about:
    1. Alternating user/assistant roles.
    2. Starting with a user message.
    3. Not supporting SystemMessage or ToolMessage roles directly.
    """
    combined = []
    system_text = ""
    
    # 1. Categorize messages
    for msg in messages:
        if isinstance(msg, SystemMessage):
            system_text += str(msg.content) + "\n"
        elif isinstance(msg, ToolMessage):
            # Convert tool output to a user message
            content = f"Tool output: {str(msg.content)}"
            combined.append({"role": "user", "content": content})
        elif isinstance(msg, AIMessage):
            combined.append({"role": "assistant", "content": str(msg.content)})
        elif isinstance(msg, HumanMessage):
            combined.append({"role": "user", "content": str(msg.content)})
        else:
            # Fallback for other message types
            content = str(msg.content) if hasattr(msg, "content") else str(msg)
            combined.append({"role": "user", "content": content})

    # 2. Merge consecutive roles to ensure alternation
    merged = []
    for m in combined:
        if merged and merged[-1]["role"] == m["role"]:
            merged[-1]["content"] += "\n" + m["content"]
        else:
            merged.append(m)
            
    # 3. Prepend system prompt to the first user message
    if system_text:
        user_idx = -1
        for i, m in enumerate(merged):
            if m["role"] == "user":
                user_idx = i
                break
        
        if user_idx != -1:
            merged[user_idx]["content"] = f"{system_text.strip()}\n---\n{merged[user_idx]['content']}"
        else:
            # No user message found, create one from the system prompt
            merged.insert(0, {"role": "user", "content": system_text.strip()})

    # 4. Final check: Ensure it starts with user
    if merged and merged[0]["role"] == "assistant":
        merged.insert(0, {"role": "user", "content": "Follow up on the following conversation:"})

    # 5. Convert back to LangChain messages for model.invoke
    lc_messages = []
    for m in merged:
        if m["role"] == "user":
            lc_messages.append(HumanMessage(content=m["content"]))
        else:
            lc_messages.append(AIMessage(content=m["content"]))
            
    return lc_messages

def call_model(state: AgentState):
    original_messages = state["messages"]
    
    # Sanitize the history for Sarvam AI's strict requirements
    sanitized_messages = sanitize_messages_for_sarvam(original_messages)
    
    # Call the model
    response = model_with_tools.invoke(sanitized_messages)
    
    # Check if we need to parse manual tool calls
    content = response.content
    if isinstance(content, str) and "```tool_call" in content:
        # Extract JSON from the code block - handle potential variations
        match = re.search(r"```tool_call\s*\n?(.*?)\n?```", content, re.DOTALL)
        if match:
            try:
                raw_json = match.group(1).strip()
                tool_data = json.loads(raw_json)
                
                # Ensure it's a list even if model gave a single object
                if isinstance(tool_data, dict):
                    tool_data = [tool_data]
                
                tool_calls = []
                for i, call in enumerate(tool_data):
                    tool_calls.append({
                        "name": call["name"],
                        "args": call["arguments"],
                        "id": f"call_{len(original_messages)}_{i}"
                    })
                
                response.tool_calls = tool_calls
                print(f"DEBUG: Parsed Tool Calls: {tool_calls}")
            except Exception as e:
                print(f"DEBUG: Error parsing tool call: {e}, Raw: {match.group(1)}")
    
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
