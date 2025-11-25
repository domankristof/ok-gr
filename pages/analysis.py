import pandas as pd
import streamlit as st
import numpy as np

from core.gr_agent import run_agent
from core.load_telemetry import load_parquet_from_supabase_filtered

from core.determine_reference_tool import compute_reference_laps
from core.delta_tool import deltas_tool, time_to_seconds

from core.summary_key_stats import display_key_summary_stats
from core.summary_weather import render_weather_summary
from core.summary_telemetry import summarize_telemetry
from core.summary_deltas import summary_deltas
from core.summary_telemetry import speed_distance_plot
from core.summary_telemetry import gg_plot


# =========================================================
# PAGE CONFIG (MUST COME FIRST)
# =========================================================
st.set_page_config(
    page_title="Analysis - OK GR",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# =========================================================
# REQUIRED SESSION STATE VARIABLES
# =========================================================
required = ["car_number", "laps_file", "weather_file", "sectors_file", "telemetry_session"]

missing = [r for r in required if r not in st.session_state or st.session_state[r] in [None, ""]]

if missing:
    st.error("⚠️ Missing required data:")
    st.write(missing)
    st.stop()


# =========================================================
# CAR NUMBER
# =========================================================
raw_car = st.session_state.get("car_number")

try:
    car_number = int(str(raw_car).strip())
except:
    st.error("Invalid car number.")
    st.stop()


laps_file = st.session_state.laps_file
weather_file = st.session_state.weather_file
results_file = st.session_state.get("results_file")
sectors_file = st.session_state.sectors_file


# =========================================================
# TELEMETRY FILE MAPPING
# =========================================================
telemetry_map = {
    "Virginia International Raceway - Race 1": "r1_vir_telemetry_data.parquet",
    "Virginia International Raceway - Race 2": "r2_vir_telemetry_data.parquet",

    "Indianapolis Motor Speedway - Race 1": "r1_indianapolis_motor_speedway_telemetry.parquet",
    "Indianapolis Motor Speedway - Race 2": "r2_indianapolis_motor_speedway_telemetry.parquet",

    "Circuit of The Americas - Race 1": "r1_cota_telemetry_data.parquet",
    "Circuit of The Americas - Race 2": "r2_cota_telemetry_data.parquet",
}

session_name = st.session_state.telemetry_session

if session_name not in telemetry_map:
    st.error("Unknown telemetry session.")
    st.stop()

parquet_file_name = telemetry_map[session_name]


# =========================================================
# CAR-ONLY TELEMETRY LOADER (CACHED)
# =========================================================
@st.cache_resource(show_spinner="Loading telemetry for this car…")
def load_car_telemetry(parquet_name: str, car_number: int):
    minimal_cols = ["timestamp", "vehicle_number", "telemetry_name", "telemetry_value","lap"]

    # Load ONLY these columns (memory-safe)
    df = load_parquet_from_supabase_filtered(parquet_name, minimal_cols)

    # Filter to car number
    df = df[df["vehicle_number"] == car_number]

    return df


# =========================================================
# LOAD TELEMETRY INTO SESSION
# =========================================================
if "telemetry_file" not in st.session_state:
    try:
        st.session_state.telemetry_file = load_car_telemetry(
            parquet_file_name,
            car_number
        )
    except Exception as e:
        st.error(f"Telemetry load failed: {e}")
        st.stop()

telemetry_file = st.session_state.telemetry_file

#-------------------------------------------------------------
# Apply CSS
#-------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;700&display=swap');

:root{
  --bg:#0B0D10;            /* night track */
  --panel:#12151A;         /* pit-wall console */
  --muted:#1A1F26;         /* shadow panels */
  --text:#E6EAF0;          /* light text */
  --subtle:#98A2B3;        /* secondary text */
  --accent:#E10600;        /* F1 red */
  --neon:#23F0C7;          /* telemetry neon */
  --good:#2ED573;
  --warn:#FFC107;
  --bad:#FF4757;
  --border:#262C36;
}

html, body, [data-testid="stAppViewContainer"] {
  background: radial-gradient(1200px 800px at 10% -10%, #12151A 0%, #0B0D10 45%) no-repeat var(--bg);
  color: var(--text);
  font-family: 'Rajdhani', ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Helvetica Neue, Arial, "Apple Color Emoji","Segoe UI Emoji","Segoe UI Symbol";
}

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0E1116 0%, #0B0D10 100%);
  border-right: 1px solid var(--border);
}

h1, h2, h3, h4, h5 { letter-spacing: 0.5px; }

.hr-line {
  height: 1px; background: linear-gradient(0deg, transparent, var(--border), transparent);
  margin: 0.8rem 0 1.2rem 0;
}

/* Checkered banner */
.banner {
  position: relative;
  padding: 18px 22px;
  border-radius: 12px;
  background: linear-gradient(180deg, #12151A 0%, #0E1014 100%);
  border: 1px solid var(--border);
  overflow: hidden;
}
.banner:before {
  content: "";
  position: absolute;
  top: 0; right: -80px;
  width: 820px; height: 100%;
  background:
    linear-gradient(135deg, rgba(255,255,255,0.05) 25%, transparent 25%) -20px 0/40px 40px,
    linear-gradient(225deg, rgba(255,255,255,0.05) 25%, transparent 25%) -20px 0/40px 40px,
    linear-gradient(315deg, rgba(255,255,255,0.05) 25%, transparent 25%) 0 0/40px 40px,
    linear-gradient(45deg, rgba(255,255,255,0.05) 25%, transparent 25%) 0 0/40px 40px;
  transform: rotate(-10deg);
  opacity: 0.6;
}
.badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--accent);
  color: white; font-weight: 700; font-size: 12px;
  letter-spacing: .4px;
}

/* Cards */
.card {
  border: 1px solid var(--border);
  background: linear-gradient(180deg, #101319 0%, #0C0F14 100%);
  border-radius: 14px;
  padding: 14px 16px;
}
.card h4{
  margin: 0 0 6px 0; color: var(--text); font-weight: 700;
}
.card .meta{ color: var(--subtle); font-size: 13.5px; }
.card .ok { color: var(--good); font-weight: 700; }
.card .miss { color: var(--warn); font-weight: 700; }

/* Upload box tweak */
.css-1v0mbdj, .e1b2p2ww15 { border-radius: 12px !important; }
            
.stFileUploader>div>div {
    background-color: #12151A;
    border: 2px dashed #262C36;
    border-radius: 10px;
    color: #ffffff;
    }

/* Hide the label since you're using label_visibility="hidden" */
.stFileUploader label {
    display: none;
}

.stButton>button {
    background-color: var(--accent);
    color: white;
    font-weight: 700;
    border-radius: 8px;
    border: none;
}
.stButton>button:hover {
    background-color: #bf0500;
}
</style>
            
<style>
.chat-container {
    height: 70vh;      /* Adjust height */
    overflow-y: auto;  /* Scrollable */
    padding-bottom: 70px;  /* Space so chat input doesn't overlap */
}

/* 1. Target the main metric container for background and border */
[data-testid="stMetric"] {
    position: relative;
    padding: 18px 22px;
    background-color: linear-gradient(180deg, #12151A 0%, #0E1014 100%);
    border: 1px solid var(--border);
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
    /* Set a min width to ensure uniform size in columns */
    min-width: 150px;
    min-height: 90px;
}
</style>

""", unsafe_allow_html=True)

# ----------------------------
# Header
# ----------------------------
st.markdown("""
    <div class="banner" style="position: relative; padding-right: 50px;">
    <span class="badge">Toyota Gazoo Racing</span>
    <img src="https://upload.wikimedia.org/wikipedia/commons/e/e6/Toyota_Gazoo_Racing_emblem.svg"
        style="position: absolute; top: 20px; right: 15px; height: 40px; width: auto;">
    <div style="text-align: left;">
        <h1 style="margin:0;font-weight:800;">Session Analysis</h1>
        <div style="color:#23F0C7;font-weight:400;margin-top:0px;">GR Agent Ready</div>
    </div>
    </div>
    """, unsafe_allow_html=True)
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)


#Split Screen
left,right = st.columns([1,1], gap="medium",width="stretch", vertical_alignment="top")

#--------------------------------------------
# Right Side - Race Engineer Chat
#--------------------------------------------
with right:
    st.subheader("Chat with Your Engineer")
    st.markdown('<div class="hr-line"></div>', unsafe_allow_html=True)

    ENGINEER_AVATAR = "https://i.postimg.cc/DwpKJR59/race-engineer.png"
    DRIVER_AVATAR = "https://i.postimg.cc/PfVb743X/gr-driver.png"

    SYSTEM_PROMPT = """
    You are “GR-Agent” — an elite race engineer for Toyota Gazoo Racing.
    Your role is to analyse telemetry, racing data, lap traces, sector deltas, and driver inputs to provide world-class coaching and actionable feedback.
    You communicate with the tone, clarity, and confidence of a real race engineer on the pit wall.
    You are calm, concise, brutally honest, and fully focused on finding performance.
    You are a seasoned race engineer with experience in F1, GT Racing and Rally.
    You are an English gentleman.

    1. Personality & Communication Style

    You MUST communicate with the following personality traits:
    Calm, confident, analytical — like a top-level F1/IMSA race engineer.
    Concise — no long essays; give short, sharp, actionable insights.
    Direct but supportive — “Here’s where we’re losing time. Here’s how to fix it.”
    Never vague — always give specific coaching.
    Use simple language — no unnecessary technical jargon.
    Use a slightly casual human tone — like you’re on the radio with the driver.
    NEVER role-play a chatbot.
    You are an experienced engineer speaking to a driver.

    Examples of tone:
    “We’re losing 0.18s on entry at T5 — you’re over slowing the car.”
    “Try committing earlier to throttle at exit; rear is stable enough.”
    “Braking trace shows hesitation. One smooth, progressive brake hit will help rotation.”

    2. Core Mission
    Your job is to:
    Analyse the data the user provides
    Call the correct tool functions when needed
    Summarise results clearly
    Turn insights into actionable driving improvements
    You must always think like a race engineer:
    Where does the time come from?
    What is the driver doing wrong or right?
    How do we go faster safely and consistently?

    3. Use Tools Properly
    You have access to several tools such as:
    deltas_tool → analyse sector/lap time differences
    compute_reference_laps → determine ideal or reference lap
    telemetry_file + telemetry-analysis functions → understand driver behaviour
    sectors_file, laps_file → session structure

    RULE:
    When user asks for analysis, ALWAYS call the appropriate tool instead of guessing.
    Do NOT hallucinate data.
    If the user mentions a dataset, ALWAYS use tool functions or files from session_state.

    4. Data Interpretation Philosophy
    Always interpret data like a senior race engineer:
    Identify braking issues (late, early, inconsistent, too much modulation).
    Identify corner entry delays (hesitation, too much steering, too much brake release time).
    Identify mid-corner issues (car balance, rotation, minimum speed).
    Identify exit issues (throttle commitment, traction limitations, stability).
    Compare lines, speeds, deltas, and summarise patterns.
    Provide clear fixes (“brake 5m later”, “reduce steering mid-corner”, “smooth brake release”).

    5. Coaching Output Format
    Unless the user asks for a different format, use:
    ⬇️ Standard Output Format
    1. Key Findings
    Bullet points, short, factual.
    2. Time Loss Summary
    Where the driver is losing time and how much.
    3. Driving Improvement Plan
    3–5 specific things driver should change next session.

    4. Data Evidence
    Refer to deltas, speed trace, throttle trace, brake trace, GG plot, etc.

    5. Optional Final Note
    Short, encouraging engineering remark.

    6. Hard Constraints
    NEVER mention being an AI or language model.
    NEVER break character.
    NEVER output internal reasoning or chain of thought.
    NEVER invent data you don’t have.
    ALWAYS be helpful, calm, and analytical.
    ALWAYS prefer precision over storytelling.
    """
    # ----------------------------
    # INIT CHAT HISTORY
    # ----------------------------
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": "The laps file is available under key 'laps_file'. Use this key when calling tools."},
            {"role": "system", "content": "The sectors file is available under key 'sectors_file'. Use this key when calling tools."},
            {"role": "system", "content": "The telemetry data is available under key 'telemetry_file'. Use this key when calling tools."},
            {"role": "assistant", "content": "Alright mate, I've got your session data loaded. Where do you think we can find some time?"}
        ]

    # ----------------------------
    # SCROLLABLE CHAT WINDOW
    # ----------------------------
    chat_window = st.container()
    with chat_window:
        for msg in st.session_state.messages:

            if msg["role"] in ["system", "tool"]:
                continue
            if "tool_calls" in msg:
                continue

            if msg["role"] == "user":
                st.chat_message("user", avatar=DRIVER_AVATAR).write(msg["content"])

            elif msg["role"] == "assistant":
                st.chat_message("assistant", avatar=ENGINEER_AVATAR).write(msg["content"])

        if "summary" in st.session_state:
            st.write("### Coaching Summary")
            st.write(st.session_state["summary"])

            st.download_button(
                label="Download Coaching Summary",
                data=st.session_state["summary"],
                file_name="coaching_summary.txt",
                mime="text/plain"
            )

    # ----------------------------
    # CHAT INPUT 
    # ----------------------------
    prompt = st.chat_input("Ask anything about your race data…", key="race_chat_input")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})

        clean_history = [
            m for m in st.session_state.messages
            if m["role"] != "tool"
        ]

        response = run_agent(clean_history)

        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })

        st.rerun()
# ----------------------------
# Left Side - Session Analysis
# ----------------------------
with left:
    st.subheader("Data Summary")
    st.markdown('<div class="hr-line"></div>', unsafe_allow_html=True)

    speed_distance_plot(telemetry_file,car_number)

    #Key Summary Stats
    if laps_file is None:
        st.warning("No laps file found — upload data first.")
    else:
        try:
            stats = display_key_summary_stats(laps_file, car_number)
        except Exception as e:
            st.error(f"Error displaying summary stats: {e}")

    st.markdown('<div class="hr-line"></div>', unsafe_allow_html=True)

    #Weather Summary
    if weather_file is None:
        st.warning("No weather file found — upload data first.")
    else:
        try:
            weather_summary = render_weather_summary(weather_file)
        except Exception as e:
            st.error(f"Error displaying weather summary: {e}")

    st.markdown('<div class="hr-line"></div>', unsafe_allow_html=True)
        #Summary Telemetry
    try:
        telemetry_summary = gg_plot(telemetry_file, car_number)
    except Exception as e:
        st.error(f"Error loading telemetry data: {e}")

    summary_of_deltas = summary_deltas(sectors_file, car_number)

    st.markdown('<div class="hr-line"></div>', unsafe_allow_html=True)

