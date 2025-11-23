from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import streamlit as st

# ---- Import your actual tool functions from your core files ----
from core.determine_reference_tool import compute_reference_laps as ref_laps_tool
from core.delta_tool import deltas_tool as core_deltas_tool
from core.delta_tool import time_to_seconds as core_time_to_seconds


# ----------------------------
# Environment & Client Setup
# ----------------------------
load_dotenv()
client = OpenAI(api_key=os.getenv("OPEN_AI_KEY"))


# ----------------------------
# TOOL WRAPPERS
# ----------------------------

def tool_compute_reference_laps(laps_key: str, car_number: int):
    """
    Wrapper around compute_reference_laps(), retrieving the file
    from Streamlit session state and handling errors safely.
    """
    if laps_key not in st.session_state:
        return {"status": "error", "message": f"No file found for key '{laps_key}'"}

    file_obj = st.session_state[laps_key]

    try:
        result = ref_laps_tool(file_obj, car_number)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def tool_compute_deltas(sectors_key: str, car_number: int):
    """
    Wrapper for your deltas tool. Ensures JSON compatibility.
    """
    if sectors_key not in st.session_state:
        return {"status": "error", "message": f"No file found for key '{sectors_key}'"}

    file_obj = st.session_state[sectors_key]

    try:
        file_obj.seek(0)

        result = core_deltas_tool(file_obj, car_number)

        # Convert DataFrames inside result → JSON
        if "deltas" in result and hasattr(result["deltas"], "to_dict"):
            result["deltas"] = result["deltas"].to_dict(orient="records")

        return {"status": "success", "data": result}

    except Exception as e:
        return {"status": "error", "message": str(e)}


def tool_time_to_seconds(t: str):
    """Simple wrapper around your core time parser."""
    try:
        return {"seconds": core_time_to_seconds(t)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ----------------------------
# OpenAI Tool Definitions
# ----------------------------
tools = [
    {
        "type": "function",
        "function": {
            "name": "tool_compute_reference_laps",
            "description": "Compute reference laps for a given car number from the uploaded laps file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "laps_key": {
                        "type": "string",
                        "description": "Key for the laps CSV in Streamlit session_state"
                    },
                    "car_number": {
                        "type": "integer",
                        "description": "Driver's car number"
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
            "description": "Compute lap deltas, sector deltas, optimal lap time, and consistency score.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sectors_key": {
                        "type": "string",
                        "description": "Key for the sectors CSV in Streamlit session_state"
                    },
                    "car_number": {
                        "type": "integer",
                        "description": "Car number to compute deltas for"
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
            "description": "Convert a time string (e.g. '1:25.342') into seconds.",
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

# Map tool names to Python functions
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
