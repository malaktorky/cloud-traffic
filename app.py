import streamlit as st
import tempfile
import cv2
from ultralytics import YOLO

st.title("🚦 Smart Traffic Cloud")

uploaded_file = st.file_uploader("Upload Video", type=["mp4", "avi"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(uploaded_file.read())
        video_path = tmp.name

    st.video(video_path)

    if st.button("Run Detection"):
        model = YOLO("yolov8n.pt")

        cap = cv2.VideoCapture(video_path)

        output = "output.mp4"
        out = cv2.VideoWriter(
            output,
            cv2.VideoWriter_fourcc(*"mp4v"),
            20,
            (640, 480)
        )

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            results = model(frame)

            for r in results:
                for box in r.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(frame, (x1,y1),(x2,y2),(0,255,0),2)

            out.write(frame)

        cap.release()
        out.release()

        st.success("Done")
        st.video(output)