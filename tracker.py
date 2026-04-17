from typing import Dict, List, Tuple

Point = Tuple[int, int]
Detection = Tuple[int, int, int, int, float, int]


def compute_center(x1: int, y1: int, x2: int, y2: int) -> Point:
    return int((x1 + x2) / 2), int((y1 + y2) / 2)


class SimpleTracker:
    def __init__(self, max_distance: int = 60):
        self.next_id = 1
        self.objects: Dict[int, Dict] = {}
        self.max_distance = max_distance

    def _distance(self, c1: Point, c2: Point) -> float:
        return ((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2) ** 0.5

    def update(self, detections: List[Detection]):
        updated = []
        used_ids = set()

        for x1, y1, x2, y2, conf, cls in detections:
            cx, cy = compute_center(x1, y1, x2, y2)

            matched_id = None
            best_dist = 1e9

            for tid, obj in self.objects.items():
                if tid in used_ids:
                    continue
                if obj["cls"] != cls:
                    continue

                dist = self._distance(obj["center"], (cx, cy))
                if dist < self.max_distance and dist < best_dist:
                    best_dist = dist
                    matched_id = tid

            if matched_id is None:
                matched_id = self.next_id
                self.next_id += 1
                history = [(cx, cy)]
                stopped = 0
            else:
                prev = self.objects[matched_id]
                history = prev["history"] + [(cx, cy)]
                if len(history) > 20:
                    history = history[-20:]

                movement = self._distance(prev["center"], (cx, cy))
                stopped = prev["stopped"] + 1 if movement < 2 else 0

            self.objects[matched_id] = {
                "center": (cx, cy),
                "history": history,
                "stopped": stopped,
                "cls": cls,
                "bbox": (x1, y1, x2, y2),
            }

            used_ids.add(matched_id)

            updated.append(
                {
                    "track_id": matched_id,
                    "center": (cx, cy),
                    "history": history,
                    "stopped_frames": stopped,
                    "cls": cls,
                    "bbox": (x1, y1, x2, y2),
                }
            )

        return updated