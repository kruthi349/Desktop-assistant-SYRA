import os
import json
import re
from datetime import datetime
from langchain_core.tools import Tool, tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict, Annotated, Literal
import psutil
import platform


from engine.config import (
    GEMINI_API_KEY, ASSISTANT_NAME
)


# ==================== IMPORT TOOLS ====================
from engine.tools import all_tools



# ==================== Define State ====================
class AgentState(TypedDict):
    input: str
    output: str
    tool_results: dict


# ==================== Initialize LLM ====================
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    api_key=GEMINI_API_KEY,
    temperature=0.7
)


# Bind tools to LLM
llm_with_tools = llm.bind_tools(all_tools, tool_choice="auto")



# ==================== HELPER: Clean JSON Responses ====================
def clean_json_response(data):
    """Remove 'signature' and 'extras' from JSON responses, keep only useful text"""
    if isinstance(data, dict):
        data.pop('signature', None)
        data.pop('extras', None)
        return data
    elif isinstance(data, list):
        cleaned = []
        for item in data:
            if isinstance(item, dict):
                item.pop('signature', None)
                item.pop('extras', None)
                if 'text' in item:
                    cleaned.append(item['text'])
                else:
                    cleaned.append(item)
            else:
                cleaned.append(item)
        return cleaned
    return data



def extract_text_from_response(response):
    """Extract clean text from various response formats"""
    if isinstance(response, str):
        return response
    elif isinstance(response, dict):
        if 'text' in response:
            return response['text']
        for key, value in response.items():
            if key not in ['signature', 'extras'] and isinstance(value, str):
                return value
        return str(response)
    elif isinstance(response, list):
        texts = []
        for item in response:
            if isinstance(item, dict) and 'text' in item:
                texts.append(item['text'])
            elif isinstance(item, str):
                texts.append(item)
        return " ".join(texts) if texts else str(response)
    return str(response)


def summarize_with_llm(tool_name: str, tool_result: str, user_query: str) -> str:
    """Pass tool results through LLM for concise, natural responses"""
    try:
        summary_prompt = f"""You are a helpful assistant. The user asked: "{user_query}"
        
Tool '{tool_name}' returned: {tool_result}

Provide a SHORT, NATURAL response (1-2 sentences max) that directly answers the user's question.
Be conversational and concise. Don't mention the tool name."""

        response = llm.invoke(summary_prompt)
        return response.content if hasattr(response, 'content') else str(response)
    except Exception as e:
        return tool_result  # Fallback to original result



# ==================== Create Agent ====================
def create_agent():
    """Create agent - processes tool calls within chat node, no separate routing"""
    
    system_prompt = f"""You are {ASSISTANT_NAME}, an intelligent AI assistant.


IMPORTANT INSTRUCTIONS:
1. Tasks are stored in a DICTIONARY organized by DATE  
2. For task management, use the provided task tools:
   - fetch_tasks(time_filter): Get tasks ("today", "tomorrow", "upcoming", "all")
   - add_new_task(title, date): Add new task
   - complete_task_by_id(task_id): Mark task complete
   - delete_task_by_id(task_id): Delete task
   - get_current_datetime(): Get current date/time


3. Extract parameters clearly:
   - Weather: Extract CITY name
   - Stock: Extract SYMBOL (convert to uppercase)
   - WhatsApp/SMS: Extract CONTACT NAME and MESSAGE
   - Tasks: Extract TASK ID (numbers) or TITLE (text)


4. Always provide SHORT, NATURAL responses  
5. When a tool returns data, summarize it conversationally  
6. Ask for clarification if parameters are missing  


7. SMART SEARCH (3 Types):
   - Wikipedia summaries: search_wikipedia("topic")
   - Google search: search_google("query")
   - YouTube videos: search_youtube("video name")


8. SYSTEM MONITORING & CONTROL:
   - Control brightness: control_brightness("increase"/"decrease"/"set", value)
   - Control volume: control_volume("increase"/"decrease"/"set"/"mute", value)
   - Check battery: get_battery_status()
   - Check ram: get_ram_usage()
   - Check cpu usage: get_cpu_usage()
   - Check system stats: get_system_stats()
   - Take screenshot: take_screenshot()


9. Email:
   - Generate meaningful subject and body
   - THEN call send_email(to=<address>, message_summary=<summary>)


10. FOLDER & FILE CREATION:
   - To create a folder → create_folder(folder_name="name")
   - To delete a folder → delete_folder(folder_name="name")
   - To generate code/text and save file → create_file(instruction="what to generate")

    When using create_file:
    - NEVER provide "EXTENSION" or "CONTENT" in the tool call.
    - ALWAYS pass only: create_file(instruction="user request")
    The tool itself queries an LLM internally to generate extension + content.


11. TASK COMMAND EXAMPLES:
    - "Show today's tasks" → fetch_tasks(time_filter="today")
    - "Add task buy groceries" → add_new_task(title="buy groceries")
    - "Complete task 1" → complete_task_by_id(task_id=1)
    - "Delete task 3" → delete_task_by_id(task_id=3)


12. SPECIAL WORKFLOW:
    Fetch my WhatsApp chats:
        1. open Whatsapp  
        2. take a screenshot  
        3. send screenshot location to LLM  
        4. extract unread chats  


GENERAL RULES:
- Be helpful, concise, actionable  
- Use tools intelligently  
- If a tool can perform the task, ALWAYS use it.  
- Never mention tool names unless necessary.  
"""

    # ==================== Define Nodes ====================
    def route_node(state: AgentState):
        """Route node - checks if a tool is required to answer the query"""
        user_input = state["input"]
        
        # Build tool list for prompt
        tool_list = []
        for tool in all_tools:
            tool_list.append({
                "name": tool.name,
                "description": tool.description if hasattr(tool, 'description') else "No description"
            })
        
        # System prompt for tool requirement detection
        tool_detection_prompt = f"""You are a tool requirement analyzer. Analyze the user's query and determine:

1. Is a tool/function call required to answer this query?
2. If yes, which tool from this list would be needed?

Available tools:
{json.dumps(tool_list, indent=2)}

User query: "{user_input}"

Respond ONLY in JSON format:
{{
    "requires_tool": true/false,
    "tool_name": "exact_tool_name_or_null",
    "reasoning": "brief explanation"
}}"""

        try:
            detection_response = llm.invoke(tool_detection_prompt)
            response_text = detection_response.content if hasattr(detection_response, 'content') else str(detection_response)
            
            # Try to parse JSON from response
            try:
                # Find JSON in response
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text)
                if json_match:
                    detection_result = json.loads(json_match.group())
                else:
                    detection_result = json.loads(response_text)
            except (json.JSONDecodeError, ValueError):
                # If JSON parsing fails, assume no tool needed
                detection_result = {"requires_tool": False, "tool_name": None, "reasoning": "Could not parse tool detection"}
            
            requires_tool = detection_result.get("requires_tool", False)
            tool_name = detection_result.get("tool_name")
            reasoning = detection_result.get("reasoning", "")
            
            print(f"📍 Route Analysis: Tool Required = {requires_tool}, Tool = {tool_name}, Reason = {reasoning}")
            
            # Return updated state with routing info
            return {
                "input": user_input,
                "output": state.get("output", ""),
                "tool_results": state.get("tool_results", {})
            }
            
        except Exception as e:
            print(f"Route node error: {e}")
            import traceback
            traceback.print_exc()
            return state

    def chat_node(state: AgentState):
        """LLM node - processes user input, handles tool calls internally, and returns response"""
        user_input = state["input"]
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_input)
        ]
        
        try:
            # Get LLM response with tool bindings
            response = llm_with_tools.invoke(messages)
            
            output = response.content if hasattr(response, "content") else ""
            tool_results = {}
            
            # ==================== HANDLE TOOL CALLS ====================
            if hasattr(response, "tool_calls") and response.tool_calls:
                for tool_call in response.tool_calls:
                    tool_name = tool_call.get("name")
                    tool_args = tool_call.get("args", {})
                    
                    print(f"🔧 Calling tool: {tool_name} with args: {tool_args}")
                    
                    try:
                        # Find and execute tool
                        for tool in all_tools:
                            if tool.name == tool_name:
                                result = tool.func(**tool_args)
                                
                                # Clean JSON if needed
                                if isinstance(result, (dict, list)):
                                    result = clean_json_response(result)
                                    result = extract_text_from_response(result)
                                
                                # Convert to string for processing
                                result_str = str(result)
                                
                                # Pass through LLM for natural response
                                summarized_result = summarize_with_llm(tool_name, result_str, user_input)
                                
                                tool_results[tool_name] = summarized_result
                                print(f"✓ Tool result (summarized): {summarized_result[:100]}")
                                
                                # Use summarized result as output
                                if not output:
                                    output = summarized_result
                                
                                break
                    except Exception as e:
                        error_msg = f"Error executing {tool_name}: {str(e)}"
                        tool_results[tool_name] = error_msg
                        print(f"✗ Tool error: {error_msg}")
            
            # Cleanup final output
            if isinstance(output, (dict, list)):
                output = extract_text_from_response(output)
            
            output = str(output).strip() if output else "I couldn't process that request. Could you rephrase?"
            
            return {
                "input": user_input,
                "output": output,
                "tool_results": tool_results
            }
            
        except Exception as e:
            print(f"Chat node error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "input": user_input,
                "output": f"Error: {str(e)}",
                "tool_results": {}
            }
    
    
    # ==================== Build Graph ====================
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("route", route_node)
    graph.add_node("chat", chat_node)
    
    # Set entry point to route node
    graph.set_entry_point("route")
    
    # Route always flows to chat (route node analyzes but chat node handles execution)
    graph.add_edge("route", "chat")
    
    # Chat node is exit point
    graph.add_edge("chat", END)
    
    agent = graph.compile()
    with open("agent_workflow.png", "wb") as f:
        f.write(agent.get_graph().draw_mermaid_png())
    
    return agent



# ==================== Export ====================
try:
    agent_executor = create_agent()
    print("✓ Agent created successfully")
    print("✓ IMPLEMENTATION PATTERN:")
    print("  ✓ Route node analyzes tool requirements BEFORE chat")
    print("  ✓ Route node provides intelligent tool detection")
    print("  ✓ Chat node executes tools based on LLM binding")
    print("  ✓ Tool results parsed and summarized with LLM")
    print("  ✓ Natural response generation")
    print("  ✓ Clean error handling")
    print("✓ Ready for voice commands")
except Exception as e:
    print(f"✗ Error creating agent: {e}")
    import traceback
    traceback.print_exc()
    agent_executor = None