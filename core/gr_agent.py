from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import streamlit as st

# ---- Import your actual tool functions from your core files ----
from core.determine_reference_tool import compute_reference_laps as ref_laps_tool
from core.delta_tool import deltas_tool as core_deltas_tool
from core.delta_tool import time_to_seconds as core_time_to_seconds
from core.telemetry_tools import telemetry_tool as telemetry_summary_tool


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
    

def tool_telemetry_summary(telemetry_key: str, car_number: int):
    """
    Wrapper for your telemetry summary tool. Ensures JSON compatibility.
    """
    if telemetry_key not in st.session_state:
        return {"status": "error", "message": f"No file found for key '{telemetry_key}'"}

    file_obj = st.session_state[telemetry_key]

    try:
        result = telemetry_summary_tool(file_obj, car_number)

        return {"status": "success", "data": result}

    except Exception as e:
        return {"status": "error", "message": str(e)}


def tool_time_to_seconds(t: str):
    """Simple wrapper around your core time parser."""
    try:
        return {"seconds": core_time_to_seconds(t)}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    

def tool_generate_session_summary(chat_history: str):
    """
    Takes the full chat history as a string and returns:
    - a session summary
    - coaching points
    - a downloadable text file path
    """

    from datetime import datetime

    # 1. Ask GPT to summarise and generate coaching points
    summary_prompt = f"""
    You are a race engineer. Summarise this coaching session into:
    1) Driver session summary
    2) Driving strengths
    3) Driving weaknesses
    4) Top priority coaching points (3 bullets MAX)
    5) Suggested next steps

    Chat history:
    {chat_history}
    """

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are a race engineer."},
            {"role": "user", "content": summary_prompt}
        ]
    )

    summary_text = response.choices[0].message.content

    # 2. Create a downloadable file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"coaching_summary_{timestamp}.txt"
    filepath = os.path.join("/tmp", filename)

    with open(filepath, "w") as f:
        f.write(summary_text)

    return {
        "status": "success",
        "summary": summary_text,
        "file_path": filepath
    }



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
    },

    {
        "type": "function",
        "function": {
            "name": "tool_generate_session_summary",
            "description": "Summarise the entire chat session and extract coaching points.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chat_history": {
                        "type": "string",
                        "description": "Full conversation history"
                    }
                },
                "required": ["chat_history"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "tool_telemetry_summary",
            "description": "Generate a telemetry summary for a given car number from the uploaded telemetry file. This returns data about steering smoothnes score, micro steering corrections, steering usage and more. Use this if user asks about their telemetry data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "telemetry_key": {
                        "type": "string",
                        "description": "Key for the telemetry_df in Streamlit session_state"
                    },
                    "car_number": {
                        "type": "integer",
                        "description": "Car number to generate telemetry summary for"
                    }
                },
                "required": ["telemetry_key", "car_number"]
            }
        }
    },
]

# Map tool names to Python functions
tool_map = {
    "tool_compute_reference_laps": tool_compute_reference_laps,
    "tool_compute_deltas": tool_compute_deltas,
    "tool_time_to_seconds": tool_time_to_seconds,
    "tool_generate_session_summary": tool_generate_session_summary,
    "tool_telemetry_summary": tool_telemetry_summary,
}


# ----------------------------
# Agent Persona
# ----------------------------
SYSTEM_PROMPT = """
You are a seasoned race engineer with deep experience in GT racing,
touring cars, F1, and driver development. You speak concisely, clearly, and with
engineering precision. You always provide actionable insights grounded in data,
race craft, and vehicle dynamics. You explain your reasoning like a professional
race engineer talking to a driver. When the user asks for a session summary, coaching summary, 
training summary, improvement plan, or anything similar, call the function tool_generate_session_summary and pass the entire chat history (excluding tool messages) as a single string under `chat_history`.

"""

# ----------------------------
# Agent Execution Function
# ----------------------------
def run_agent(messages: list):

    # Ensure persona
    if not any(m.get("role") == "system" for m in messages):
        messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})

    while True:

        # ---------------------------------------------------------------------
        # Prepare full chat history so GPT can pass it into tool_generate_summary
        # ---------------------------------------------------------------------
        chat_history_text = "\n".join(
            f"{m['role']}: {m['content']}"
            for m in messages
            if m["role"] != "tool"
        )

        # ---------------------------------------------------------------------
        # MAIN MODEL CALL
        # We append chat_history_text as a system message so GPT can use it
        # ---------------------------------------------------------------------
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages + [
                {
                    "role": "system",
                    "content": f"FULL_CHAT_HISTORY_START\n{chat_history_text}\nFULL_CHAT_HISTORY_END"
                }
            ],
            tools=tools,
            tool_choice="auto"
        )

        msg = response.choices[0].message

        # Basic assistant message
        msg_dict = {
            "role": msg.role,
            "content": msg.content,
        }

        # Record requested tool calls
        if msg.tool_calls:
            msg_dict["tool_calls"] = msg.tool_calls

        messages.append(msg_dict)

        # ---------------------------------------------------------------------
        # TOOL EXECUTION
        # ---------------------------------------------------------------------
        if msg.tool_calls:
            for tool_call in msg.tool_calls:

                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)

                tool_fn = tool_map[name]
                result = tool_fn(**args)

                # Special case: summary tool
                if name == "tool_generate_session_summary":
                    try:
                        summary_text = result.get("summary")
                        if summary_text:
                            st.session_state["summary"] = summary_text
                    except:
                        pass

                # Append tool result
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                })

            # Loop again to allow GPT to read tool output
            continue

        # ---------------------------------------------------------------------
        # NO TOOL CALL → FINAL ANSWER
        # ---------------------------------------------------------------------
        return msg.content