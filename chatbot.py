import json
import os
from pathlib import Path

import streamlit as st


# =========================
# Page Config
# =========================
st.set_page_config(
    page_title="Smart Traffic Chatbot",
    page_icon="🚦",
    layout="centered",
)

# =========================
# Paths
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = BASE_DIR / "data" / "outputs"

ROAD_FILES = {
    "Road 1": OUTPUTS_DIR / "road1.json",
    "Road 2": OUTPUTS_DIR / "road2.json",
    "Road 3": OUTPUTS_DIR / "road3.json",
}


# =========================
# Helpers
# =========================
def load_road_data():
    roads = {}
    missing = []

    for road_name, file_path in ROAD_FILES.items():
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    roads[road_name] = json.load(f)
            except Exception:
                missing.append(road_name)
        else:
            missing.append(road_name)

    return roads, missing


def congestion_to_number(congestion_value: str) -> int:
    mapping = {
        "LOW": 1,
        "MEDIUM": 2,
        "HIGH": 3,
    }
    return mapping.get(str(congestion_value).upper(), 3)


def compute_score(road_data: dict) -> float:
    avg_motion = float(road_data.get("avg_motion", 0))
    stopped = int(road_data.get("stopped", 0))
    congestion = str(road_data.get("congestion", "HIGH")).upper()
    incident = bool(road_data.get("incident", False))

    score = (
        avg_motion
        - (2.0 * stopped)
        - (3.0 * congestion_to_number(congestion))
        - (10.0 if incident else 0.0)
    )
    return score


def get_best_road(roads: dict) -> str | None:
    if not roads:
        return None
    return max(roads, key=lambda road_name: compute_score(roads[road_name]))


def summarize_road(road_name: str, road_data: dict) -> str:
    vehicles = road_data.get("vehicles", 0)
    stopped = road_data.get("stopped", 0)
    avg_motion = road_data.get("avg_motion", 0)
    congestion = road_data.get("congestion", "UNKNOWN")
    incident = road_data.get("incident", False)

    text = (
        f"**{road_name}**\n\n"
        f"- Vehicles: {vehicles}\n"
        f"- Stopped vehicles: {stopped}\n"
        f"- Average motion: {avg_motion}\n"
        f"- Congestion: {congestion}"
    )

    if incident:
        text += "\n- Alert: Suspected incident detected"

    return text


def build_global_summary(roads: dict) -> str:
    if not roads:
        return "No traffic data is available right now."

    best_road = get_best_road(roads)
    alerts = []

    for road_name, road_data in roads.items():
        if road_data.get("incident", False):
            alerts.append(f"- Avoid **{road_name}**: suspected incident detected.")

    response = f"✅ **Best road now: {best_road}**"

    if alerts:
        response += "\n\n⚠️ **Alerts:**\n" + "\n".join(alerts)

    return response


def answer_user_question(user_text: str, roads: dict) -> str:
    text = user_text.strip().lower()

    if not roads:
        return "No traffic files were found. Make sure road1.json, road2.json, and road3.json exist inside `data/outputs`."

    best_road = get_best_road(roads)

    if any(word in text for word in ["best", "better", "take", "choose", "go", "أفضل", "انهي", "أي", "اخد", "أخذ"]):
        response = f"✅ **Best road now: {best_road}**\n\n"

        ranked = sorted(
            roads.items(),
            key=lambda item: compute_score(item[1]),
            reverse=True
        )

        response += "**Ranking:**\n"
        for idx, (road_name, road_data) in enumerate(ranked, start=1):
            response += (
                f"{idx}. {road_name} "
                f"(Congestion: {road_data.get('congestion', 'UNKNOWN')}, "
                f"Motion: {road_data.get('avg_motion', 0)}, "
                f"Stopped: {road_data.get('stopped', 0)})\n"
            )

        return response

    if "road 1" in text or "road1" in text or "r1" in text or "طريق 1" in text:
        return summarize_road("Road 1", roads["Road 1"]) if "Road 1" in roads else "Road 1 data is not available."

    if "road 2" in text or "road2" in text or "r2" in text or "طريق 2" in text:
        return summarize_road("Road 2", roads["Road 2"]) if "Road 2" in roads else "Road 2 data is not available."

    if "road 3" in text or "road3" in text or "r3" in text or "طريق 3" in text:
        return summarize_road("Road 3", roads["Road 3"]) if "Road 3" in roads else "Road 3 data is not available."

    if any(word in text for word in ["alert", "incident", "حادث", "حوادث", "warning", "تحذير"]):
        alerts = []
        for road_name, road_data in roads.items():
            if road_data.get("incident", False):
                alerts.append(f"❌ **{road_name}** has a suspected incident.")

        if alerts:
            return "\n".join(alerts)
        return "✅ No incidents detected right now."

    if any(word in text for word in ["summary", "status", "ملخص", "الحالة", "الوضع"]):
        return build_global_summary(roads)

    return (
        "I can help with:\n\n"
        "- Best road now\n"
        "- Road 1 status\n"
        "- Road 2 status\n"
        "- Road 3 status\n"
        "- Incident alerts\n"
        "- Traffic summary"
    )


# =========================
# Custom Style
# =========================
st.markdown(
    """
    <style>
    .main {
        padding-top: 20px;
    }
    .stChatMessage {
        border-radius: 18px;
    }
    .title-box {
        text-align: center;
        padding: 10px 0 20px 0;
    }
    .title-box h1 {
        margin-bottom: 5px;
    }
    .title-box p {
        color: #888;
        font-size: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="title-box">
        <h1>🚦 Smart Traffic Chatbot</h1>
        <p>Ask about the best road, alerts, or traffic status</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================
# Load Data
# =========================
roads_data, missing_roads = load_road_data()

# =========================
# Session State
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hello. I can help you with traffic status.\n\n"
                "Try asking:\n"
                "- Best road now\n"
                "- Road 1 status\n"
                "- Is there any incident?\n"
                "- Traffic summary"
            ),
        }
    ]

# =========================
# Show chat history
# =========================
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# =========================
# Optional warning if files missing
# =========================
if missing_roads:
    st.warning(
        "Some road files are missing: " + ", ".join(missing_roads)
    )

# =========================
# Chat input
# =========================
user_prompt = st.chat_input("Type your question here...")

if user_prompt:
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    bot_reply = answer_user_question(user_prompt, roads_data)

    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    with st.chat_message("assistant"):
        st.markdown(bot_reply)