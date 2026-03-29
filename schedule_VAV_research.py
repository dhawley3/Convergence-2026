import datetime
import time

# -------------------------------
# VAV System (Room-Level Airflow)
# -------------------------------
class VAVSystem:
    def __init__(self, rooms_per_building=10):
        self.rooms_per_building = rooms_per_building
        self.airflow = {}

    def set_airflow(self, building_id, room_num, level):
        if building_id not in self.airflow:
            self.airflow[building_id] = ["LOW"] * self.rooms_per_building

        self.airflow[building_id][room_num] = level
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {building_id} Room {room_num} → {level}")

# -------------------------------
# Research Schedule (Room-Based)
# -------------------------------
class ResearchSchedule:
    def __init__(self):
        # building → room → list of (start, end)
        self.schedule = {
            "Building_A": {
                0: [("09:00", "11:00"), ("14:00", "16:00")],
                1: [("10:00", "12:00")],
                2: [("08:00", "10:00"), ("13:00", "15:00")]
            },
            "Building_B": {
                0: [("09:00", "10:30")],
                3: [("12:00", "14:00")]
            }
        }

    def get_today_schedule(self, building_id, room_num):
        today = datetime.date.today()
        result = []

        for start, end in self.schedule.get(building_id, {}).get(room_num, []):
            start_dt = datetime.datetime.combine(
                today,
                datetime.datetime.strptime(start, "%H:%M").time()
            )
            end_dt = datetime.datetime.combine(
                today,
                datetime.datetime.strptime(end, "%H:%M").time()
            )
            result.append((start_dt, end_dt))

        return result

# -------------------------------
# Smart VAV Controller
# -------------------------------
def control_vav(buildings, schedule_system, vav_system, check_interval=30):
    while True:
        now = datetime.datetime.now()

        for building in buildings:
            for room in range(vav_system.rooms_per_building):

                schedule = schedule_system.get_today_schedule(building, room)

                # Check if research is active
                active = any(start <= now <= end for start, end in schedule)

                if active:
                    vav_system.set_airflow(building, room, "HIGH")
                else:
                    vav_system.set_airflow(building, room, "LOW")

        time.sleep(check_interval)

# -------------------------------
# Initialize + Run
# -------------------------------
buildings = ["Building_A", "Building_B"]

schedule_system = ResearchSchedule()
vav_system = VAVSystem(rooms_per_building=5)

# Run simulation (short interval for demo)
control_vav(buildings, schedule_system, vav_system, check_interval=10)
