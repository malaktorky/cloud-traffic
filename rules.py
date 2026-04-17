from typing import Dict, List, Optional, Tuple

Point = Tuple[int, int]


def check_wrong_way(track_history: List[Point], min_displacement: int = 60) -> bool:
    if len(track_history) < 2:
        return False

    start_y = track_history[0][1]
    end_y = track_history[-1][1]
    dy = end_y - start_y
    return dy < -min_displacement


def check_speeding(track_history: List[Point], pixels_per_frame_threshold: float = 25.0) -> bool:
    if len(track_history) < 2:
        return False

    total = 0.0
    for i in range(1, len(track_history)):
        x1, y1 = track_history[i - 1]
        x2, y2 = track_history[i]
        total += ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

    avg = total / (len(track_history) - 1)
    return avg > pixels_per_frame_threshold


def check_red_light_violation(center: Point, stop_line_y: int, light_is_red: bool) -> bool:
    _, y = center
    return light_is_red and y > stop_line_y


def average_motion_px(track_history: List[Point]) -> float:
    if len(track_history) < 2:
        return 0.0

    total = 0.0
    for i in range(1, len(track_history)):
        x1, y1 = track_history[i - 1]
        x2, y2 = track_history[i]
        total += ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

    return total / (len(track_history) - 1)


def latest_speed_drop_ratio(track_history: List[Point]) -> float:
    if len(track_history) < 3:
        return 0.0

    x1, y1 = track_history[-3]
    x2, y2 = track_history[-2]
    x3, y3 = track_history[-1]

    prev = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    last = ((x3 - x2) ** 2 + (y3 - y2) ** 2) ** 0.5

    if prev <= 1e-6:
        return 0.0

    return max(0.0, (prev - last) / prev)


def detect_congestion(vehicle_count: int, avg_speed_px: float, stopped_count: int):
    score = 0.0

    if vehicle_count >= 10:
        score += 0.45
    elif vehicle_count >= 6:
        score += 0.25

    if avg_speed_px <= 4:
        score += 0.35
    elif avg_speed_px <= 8:
        score += 0.20

    if stopped_count >= 5:
        score += 0.25
    elif stopped_count >= 2:
        score += 0.12

    score = min(score, 1.0)

    if score >= 0.70:
        return "HIGH", score
    if score >= 0.35:
        return "MEDIUM", score
    return "LOW", score


def detect_incident_risk(
    track_history: List[Point],
    stopped_frames: int,
    nearest_dist: Optional[float],
    fps: float,
    wrong_way_flag: bool = False
):
    score = 0.0
    avg_speed = average_motion_px(track_history)
    drop = latest_speed_drop_ratio(track_history)
    stopped_sec = stopped_frames / max(fps, 1.0)

    if wrong_way_flag:
        score += 0.70

    if drop >= 0.60:
        score += 0.35
    elif drop >= 0.35:
        score += 0.20

    if stopped_sec >= 3 and avg_speed <= 2:
        score += 0.30
    elif stopped_sec >= 1.5:
        score += 0.15

    if nearest_dist is not None:
        if nearest_dist <= 45:
            score += 0.25
        elif nearest_dist <= 70:
            score += 0.12

    score = min(score, 1.0)

    if score >= 0.70:
        return "HIGH"
    if score >= 0.35:
        return "MEDIUM"
    return "LOW"


def recommend_signal_time(lane_scores: Dict[str, float], base=30, min_g=15, max_g=60):
    if not lane_scores:
        return {}

    max_s = max(lane_scores.values())
    min_s = min(lane_scores.values())
    spread = max(max_s - min_s, 1e-6)

    result = {}
    for k, s in lane_scores.items():
        norm = (s - min_s) / spread
        delta = int((norm - 0.5) * 20)
        result[k] = max(min_g, min(max_g, base + delta))

    return result