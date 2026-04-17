from ultralytics import YOLO
import cv2
import os
import math
import json
from collections import defaultdict, deque

# =========================
# PATHS
# =========================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
VIDEOS_DIR = os.path.join(DATA_DIR, "videos")
OUTPUTS_DIR = os.path.join(DATA_DIR, "outputs")

INPUT_VIDEO = os.path.join(VIDEOS_DIR, "input.mp4")
OUTPUT_VIDEO = os.path.join(OUTPUTS_DIR, "smart_traffic_core.avi")
METRICS_JSON = os.path.join(OUTPUTS_DIR, "latest_metrics.json")

MODEL_PATH = "yolov8n.pt"

# COCO classes:
# car = 2, motorcycle = 3, bus = 5, truck = 7
VEHICLE_CLASSES = [2, 3, 5, 7]

CONF_THRESHOLD = 0.45
HISTORY_LENGTH = 12
STOP_THRESHOLD = 1.5
SLOW_THRESHOLD = 5.0
STOP_CONFIRM_FRAMES = 12

FONT = cv2.FONT_HERSHEY_SIMPLEX


# =========================
# HELPER FUNCTIONS
# =========================
def euclidean_distance(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def get_center(x1, y1, x2, y2):
    return int((x1 + x2) / 2), int((y1 + y2) / 2)


def classify_motion(motion):
    if motion < STOP_THRESHOLD:
        return "STOPPED"
    elif motion < SLOW_THRESHOLD:
        return "SLOW"
    return "MOVING"


def motion_color(state):
    if state == "STOPPED":
        return (0, 0, 255)      # Red
    elif state == "SLOW":
        return (0, 255, 255)    # Yellow
    return (0, 255, 0)          # Green


def compute_motion(history):
    if len(history) < 2:
        return 0.0

    distances = []
    for i in range(1, len(history)):
        distances.append(euclidean_distance(history[i - 1], history[i]))

    return sum(distances) / len(distances) if distances else 0.0


def estimate_congestion(vehicle_count, avg_motion, stopped_count):
    if vehicle_count >= 18 and avg_motion < 4:
        return "HIGH"
    if vehicle_count >= 10 and avg_motion < 7:
        return "MEDIUM"
    if stopped_count >= 5:
        return "HIGH"
    return "LOW"


def estimate_incident(congestion, avg_motion, stopped_count):
    if stopped_count >= 5:
        return True
    if congestion == "HIGH" and avg_motion < 2.5:
        return True
    return False


def save_metrics(data):
    with open(METRICS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# =========================
# MAIN
# =========================
def run():
    print("STARTING SMART TRAFFIC...")
    print(f"PROJECT_ROOT: {PROJECT_ROOT}")
    print(f"INPUT_VIDEO : {INPUT_VIDEO}")
    print(f"OUTPUT_VIDEO: {OUTPUT_VIDEO}")

    os.makedirs(OUTPUTS_DIR, exist_ok=True)

    if not os.path.exists(INPUT_VIDEO):
        print("ERROR: Input video file does not exist.")
        print("Expected file here:")
        print(INPUT_VIDEO)
        return

    model = YOLO(MODEL_PATH)
    cap = cv2.VideoCapture(INPUT_VIDEO)

    if not cap.isOpened():
        print("ERROR: OpenCV could not open the video.")
        print("Possible reasons:")
        print("1) Wrong path")
        print("2) Corrupted video")
        print("3) Unsupported codec")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    if fps is None or fps == 0:
        fps = 25

    if width == 0 or height == 0:
        print("ERROR: Invalid video dimensions.")
        return

    print(f"Video width : {width}")
    print(f"Video height: {height}")
    print(f"Video fps   : {fps}")

    out = cv2.VideoWriter(
        OUTPUT_VIDEO,
        cv2.VideoWriter_fourcc(*"XVID"),
        fps,
        (width, height)
    )

    if not out.isOpened():
        print("ERROR: Could not create output video writer.")
        return

    history = defaultdict(lambda: deque(maxlen=HISTORY_LENGTH))
    stop_counter = defaultdict(int)
    unique_ids = set()

    frame_id = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_id += 1

        results = model.track(frame, persist=True, verbose=False)

        current_vehicle_count = 0
        motion_values = []
        stopped_confirmed = 0

        for result in results:
            if result.boxes is None:
                continue

            for box in result.boxes:
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())

                if cls_id not in VEHICLE_CLASSES or conf < CONF_THRESHOLD:
                    continue

                current_vehicle_count += 1

                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                track_id = int(box.id[0].item()) if box.id is not None else -1

                if track_id != -1:
                    unique_ids.add(track_id)

                center = get_center(x1, y1, x2, y2)

                if track_id != -1:
                    history[track_id].append(center)

                motion = compute_motion(history[track_id]) if track_id != -1 else 0.0
                state = classify_motion(motion)

                if track_id != -1:
                    if state == "STOPPED":
                        stop_counter[track_id] += 1
                    else:
                        stop_counter[track_id] = 0

                    if stop_counter[track_id] >= STOP_CONFIRM_FRAMES:
                        stopped_confirmed += 1

                motion_values.append(motion)

                color = motion_color(state)
                label = f"ID {track_id} {state}" if track_id != -1 else state

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(
                    frame,
                    label,
                    (x1, max(y1 - 8, 20)),
                    FONT,
                    0.5,
                    color,
                    2
                )

        avg_motion = sum(motion_values) / len(motion_values) if motion_values else 0.0
        congestion = estimate_congestion(current_vehicle_count, avg_motion, stopped_confirmed)
        incident = estimate_incident(congestion, avg_motion, stopped_confirmed)
        status = "INCIDENT" if incident else congestion

        cv2.putText(frame, f"Vehicles: {current_vehicle_count}", (20, 40), FONT, 0.8, (255, 255, 255), 2)
        cv2.putText(frame, f"Unique IDs: {len(unique_ids)}", (20, 70), FONT, 0.8, (255, 255, 0), 2)
        cv2.putText(frame, f"Motion: {avg_motion:.2f}", (20, 100), FONT, 0.8, (200, 200, 200), 2)
        cv2.putText(frame, f"Stopped: {stopped_confirmed}", (20, 130), FONT, 0.8, (0, 165, 255), 2)
        cv2.putText(frame, f"Status: {status}", (20, 170), FONT, 1.0, (0, 0, 255), 3)

        out.write(frame)

        save_metrics({
            "frame": frame_id,
            "vehicles": current_vehicle_count,
            "unique_ids": len(unique_ids),
            "avg_motion": round(avg_motion, 2),
            "stopped": stopped_confirmed,
            "congestion": congestion,
            "incident": incident,
            "status": status,
            "output_video": OUTPUT_VIDEO
        })

        print(f"Processed frame {frame_id}", end="\r")

    cap.release()
    out.release()

    print("\nDONE")
    print(f"Saved video: {OUTPUT_VIDEO}")
    print(f"Saved json : {METRICS_JSON}")


if __name__ == "__main__":
    run()