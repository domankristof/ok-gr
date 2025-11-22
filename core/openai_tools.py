#add this to main once tools are ready.

import os
import streamlit as st
from datetime import datetime, timedelta
from dotenv import load_dotenv
from openai import OpenAI

# ----------------------------
# Environment & Client Setup
# ----------------------------
load_dotenv()
client = OpenAI(api_key=os.getenv("OPEN_AI_KEY"))

# ----------------------------
# TOOL DEFINITIONS
# ----------------------------
def get_current_date():
    """Returns today's date."""
    return datetime.now().strftime("%Y-%m-%d")

def get_past_date(days_before: int):
    """Returns the date N days ago."""
    past = datetime.now() - timedelta(days=days_before)
    return past.strftime("%Y-%m-%d")

def get_max_sensor_value_for_a_day(sensor_id: str, date: str):
    """Mock lookup for sensor max value."""
    mock_data = {
        "2025-10-21": {"sensor_A": 999.9, "sensor_B": 50.2},
        "2025-10-24": {"sensor_A": 27.0, "sensor_B": 640.0},
    }
    try:
        value = mock_data.get(date, {}).get(sensor_id)
        return str(value) if value is not None else "No data found."
    except Exception as e:
        return f"Error: {e}"

# ----------------------------
# OpenAI Tool Descriptors
# ----------------------------
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_date",
            "description": "Return today's date.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_past_date",
            "description": "Get the date N days ago.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days_before": {"type": "integer"}
                },
                "required": ["days_before"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_max_sensor_value_for_a_day",
            "description": "Return max sensor value for a date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sensor_id": {"type": "string"},
                    "date": {"type": "string"},
                },
                "required": ["sensor_id", "date"]
            },
        },
    },
]

# Map tool names → local Python functions
tool_map = {
    "get_current_date": get_current_date,
    "get_past_date": get_past_date,
    "get_max_sensor_value_for_a_day": get_max_sensor_value_for_a_day,
}

# ----------------------------
# Streamlit UI Setup
# ----------------------------
st.title("🤖 IoT Sensor Agent (OpenAI Version)")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant",
         "content": "Hello! Ask me anything about your sensors."}
    ]

# Display history
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# ----------------------------
# Main Agent Loop
# ----------------------------
if prompt := st.chat_input("Ask about sensor data..."):
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Agent loop (multi-step tool calling)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            while True:
                # 1. Send full conversation to OpenAI
                response = client.chat.completions.create(
                    model="gpt-4.1",
                    messages=st.session_state.messages,
                    tools=tools,
                )

                msg = response.choices[0].message
                st.session_state.messages.append(msg)

                # 2. If model wants to call a tool
                if msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        name = tool_call["function"]["name"]
                        args = tool_call["function"]["arguments"]

                        python_fn = tool_map[name]
                        result = python_fn(**args)

                        # 3. Return tool result back to model
                        tool_message = {
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": str(result)
                        }
                        st.session_state.messages.append(tool_message)
                    continue  # Ask model for next step

                # 4. If finished, show final answer
                final_answer = msg.content
                st.write(final_answer)
                break
