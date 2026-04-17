import streamlit as st
import json

st.title("🚦 Smart Traffic Cloud System")

# عرض الفيديو
st.subheader("Processed Video")
video_file = open("data/output.mp4", "rb")
st.video(video_file.read())

# قراءة النتائج
with open("data/latest_metrics.json") as f:
    data = json.load(f)

st.subheader("Traffic Metrics")

st.write(f"🚗 Vehicles: {data['vehicles']}")
st.write(f"🚦 Congestion: {data['congestion']}")
st.write(f"⚠️ Incidents: {data['incidents']}")