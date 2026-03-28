import datetime
import time
import random


# Simulated dorm automation API (room-level HVAC)
class DormAutomationSystem:
    def __init__(self, rooms_per_building=10):
        self.building_status = {}
        self.rooms_per_building = rooms_per_building

    def set_hvac(self, building_id, room_num, status):
        # Initialize building status if it doesn't exist.
        if building_id not in self.building_status:
            self.building_status[building_id] = ["OFF"] * self.rooms_per_building

        self.building_status[building_id][room_num] = status
        print(
            f"[{datetime.datetime.now().strftime('%H:%M:%S')}] "
            f"HVAC in {building_id}, Room {room_num} set to {status}"
        )

    def get_status(self, building_id, room_num):
        return self.building_status.get(building_id, ["OFF"] * self.rooms_per_building)[room_num]


# Simulated occupancy system (random test data for rooms)
class OccupancySystem:
    def __init__(self, rooms_per_building=10):
        self.rooms_per_building = rooms_per_building
        # Example: building -> list of occupancy probabilities (0-1) for each room.
        self.occupancy = {
            "Building_A": [random.random() for _ in range(self.rooms_per_building)],
            "Building_B": [random.random() for _ in range(self.rooms_per_building)],
        }

    def get_occupied(self, building_id):
        return self.occupancy.get(building_id, [0] * self.rooms_per_building)


# Integration layer for room-level HVAC control
def control_buildings(buildings, registrar, bas, check_interval=60):
    while True:
        for building in buildings:
            occupied_list = registrar.get_occupied(building)
            for room_num, occupancy_prob in enumerate(occupied_list):
                occupied = occupancy_prob > 0.5
                status = "ON" if occupied else "OFF"
                bas.set_hvac(building, room_num, status)
        time.sleep(check_interval)


# Initialize systems
buildings = ["Building_A", "Building_B"]
registrar = OccupancySystem()
bas = DormAutomationSystem()

# For testing, you might run:
# control_buildings(buildings, registrar, bas, check_interval=10)
