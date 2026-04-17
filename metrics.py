from typing import Dict, Set


class TrafficMetrics:
    def __init__(self):
        self.total_vehicles: Set[int] = set()
        self.wrong_way_ids: Set[int] = set()
        self.speeding_ids: Set[int] = set()
        self.red_light_ids: Set[int] = set()
        self.high_risk_ids: Set[int] = set()
        self.medium_risk_ids: Set[int] = set()

    def register_vehicle(self, tid: int):
        self.total_vehicles.add(tid)

    def register_wrong_way(self, tid: int):
        self.wrong_way_ids.add(tid)

    def register_speeding(self, tid: int):
        self.speeding_ids.add(tid)

    def register_red_light(self, tid: int):
        self.red_light_ids.add(tid)

    def register_high_risk(self, tid: int):
        self.high_risk_ids.add(tid)

    def register_medium_risk(self, tid: int):
        if tid not in self.high_risk_ids:
            self.medium_risk_ids.add(tid)

    def summary(self) -> Dict[str, int]:
        return {
            "total_vehicles": len(self.total_vehicles),
            "wrong_way_count": len(self.wrong_way_ids),
            "speeding_count": len(self.speeding_ids),
            "red_light_violations": len(self.red_light_ids),
            "high_risk_count": len(self.high_risk_ids),
            "medium_risk_count": len(self.medium_risk_ids),
        }