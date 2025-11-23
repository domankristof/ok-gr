from openai import OpenAI
from dotenv import load_dotenv
import os
import json

import streamlit as st

from core.determine_reference import compute_reference_laps as ref_laps_tool
from core.delta_tool import deltas_tool as core_deltas_tool
from core.delta_tool import time_to_seconds as core_time_to_seconds

# ----------------------------
# Environment & Client Setup
# ----------------------------
load_dotenv()
client = OpenAI(api_key=os.getenv("OPEN_AI_KEY"))


# ----------------------------
# TOOL Wrappers
# ----------------------------

def tool_compute_reference_laps(laps_key: str, car_number: int):
    """Wrapper for computing reference laps."""

    if laps_key not in st.session_state:
        return {"status": "error", "message": f"No file found for key '{laps_key}'"}

    laps_file_obj = st.session_state[laps_key]

    try:
        result = ref_laps_tool(laps_file_obj, car_number)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def tool_compute_deltas(sectors_key: str, car_number: int):
    """Wrapper for the delta tool."""

    if sectors_key not in st.session_state:
        return {"status": "error", "message": f"No file found for key '{sectors_key}'"}

    file_obj = st.session_state[sectors_key]

    try:
        result = core_deltas_tool(file_obj, car_number)

        # Ensure JSON safe
        result["deltas"] = result["deltas"].to_dict(orient="records")

        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def tool_time_to_seconds(t: str):
    """Convert time string to seconds."""
    try:
        return {"seconds": core_time_to_seconds(t)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ----------------------------
# OpenAI Tool Descriptors
# ----------------------------
tools = [
    {
        "type": "function",
        "function": {
            "name": "tool_compute_reference_laps",
            "description": "Compute reference laps for a given car number from the laps file. Use this when the driver asks about their best lap time or the best lap time in the session.",
            "parameters": {
                "type": "object",
                "properties": {
                    "laps_key": {
                        "type": "string",
                        "description": "Key to the laps file in Streamlit session state."
                    },
                    "car_number": {
                        "type": "integer",
                        "description": "Car number to compute reference laps for."
                    }
                },
                "required": ["laps_key", "car_number"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "tool_compute_deltas",
            "description": "Compute driver deltas, consistency, optimal lap, sector losses, and leader comparisons. Use this when the driver is asking about their sector times, optimal lap, sector times compared to the leader, or consistency.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sectors_key": {
                        "type": "string",
                        "description": "Key to the sectors file in Streamlit session state."
                    },
                    "car_number": {
                        "type": "integer",
                        "description": "Car number to compute deltas for."
                    }
                },
                "required": ["sectors_key", "car_number"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "tool_time_to_seconds",
            "description": "Convert time string 'M:SS.sss' to total seconds.",
            "parameters": {
                "type": "object",
                "properties": {
                    "t": {"type": "string"}
                },
                "required": ["t"]
            }
        }
    }
]

# ----------------------------
# Map tool names → local Python functions
# ----------------------------
tool_map = {
    "tool_compute_reference_laps": tool_compute_reference_laps,
    "tool_compute_deltas": tool_compute_deltas,
    "tool_time_to_seconds": tool_time_to_seconds
}


# ----------------------------
# Agent Persona
# ----------------------------
SYSTEM_PROMPT = """
You are a seasoned race engineer with deep experience in GT racing,
touring cars, F1, and driver development. You speak concisely, clearly, and with
engineering precision. You always provide actionable insights grounded in data,
race craft, and vehicle dynamics. You explain your reasoning like a professional
race engineer talking to a driver.
"""

# ----------------------------
# Agent Execution Function
# ----------------------------
def run_agent(messages: list):
    # Ensure persona
    if not any(m.get("role") == "system" for m in messages):
        messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})

    while True:
        # Call OpenAI
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        msg = response.choices[0].message

        # Convert to simple dict
        msg_dict = {
            "role": msg.role,
            "content": msg.content,
        }

        # If the assistant is requesting a tool call
        if msg.tool_calls:
            msg_dict["tool_calls"] = msg.tool_calls

        # Add assistant message to chat history
        messages.append(msg_dict)

        # ------------------------------
        # HANDLE TOOL CALLS
        # ------------------------------
        if msg.tool_calls:
            for tool_call in msg.tool_calls:

                # Extract name (NEW SDK)
                name = tool_call.function.name

                # Extract args (NEW SDK)
                args = json.loads(tool_call.function.arguments)

                # Call your Python function
                tool_fn = tool_map[name]
                result = tool_fn(**args)

                # Append tool message IMMEDIATELY after assistant tool call
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                })

            # After adding all tool results, continue the loop
            continue

        # No tool calls → final model answer
        return msg.content
