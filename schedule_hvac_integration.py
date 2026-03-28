import datetime
import time

# Simulated building automation API
class BuildingAutomationSystem:
   def __init__(self):
       self.building_status = {}

   def set_hvac(self, building_id, status):
       self.building_status[building_id] = status
       print(f"[{datetime.datetime.now()}] HVAC in {building_id} set to {status}")

   def get_status(self, building_id):
       return self.building_status.get(building_id, "unknown")

# Simulated registrar schedule API
class RegistrarSystem:
   def __init__(self):
       # Example schedule: building -> list of (start_time, end_time)
       self.schedule = {
           "Building_A": [("09:00", "10:30"), ("13:00", "14:30")],
           "Building_B": [("08:00", "09:00"), ("15:00", "16:00")],
       }

   def get_today_schedule(self, building_id):
       today = datetime.date.today()
       # Convert times to datetime objects for today
       schedule_today = []
       for start, end in self.schedule.get(building_id, []):
           start_dt = datetime.datetime.combine(today, datetime.datetime.strptime(start, "%H:%M").time())
           end_dt = datetime.datetime.combine(today, datetime.datetime.strptime(end, "%H:%M").time())
           schedule_today.append((start_dt, end_dt))
       return schedule_today

# Integration layer
def control_buildings(buildings, registrar, bas, check_interval=60):
   while True:
       now = datetime.datetime.now()
       for building in buildings:
           schedule = registrar.get_today_schedule(building)
           # Determine if building is occupied
           occupied = any(start <= now <= end for start, end in schedule)
           if occupied:
               bas.set_hvac(building, "ON")
           else:
               bas.set_hvac(building, "OFF")
       time.sleep(check_interval)  # check every minute

# Initialize systems
buildings = ["Building_A", "Building_B"]
registrar = RegistrarSystem()
bas = BuildingAutomationSystem()

# Run integration layer (this would normally run on a server)
# For testing, you might want to run control_buildings(buildings, registrar, bas, check_interval=10)
#control_buildings(buildings, registrar, bas, check_interval=10)
