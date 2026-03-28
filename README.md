# Academic Building HVAC Controller

This project provides a Python HVAC control loop that turns HVAC off when sensors do not detect occupancy.

## How it works

- Each zone has one or more occupancy sensors.
- If any sensor in a zone reports occupied, zone HVAC is ON.
- If no sensors report occupied, zone HVAC turns OFF.
- Building HVAC is ON if any zone is ON, otherwise OFF.

## Files

- `hvac_system.py`: Main control loop and HVAC state logic.
- `sensors.json`: Sample input payload for buildings, zones, and sensors.
- `tests/test_hvac_system.py`: Automated test cases for HVAC behavior.
- `test_dashboard.py`: Localhost web dashboard that displays test results.
- `academic_hvac_localhost.py`: Separate localhost server for checking and updating academic building HVAC ON/OFF status.

## Run

```bash
cd /Users/drewhawley/academic-energy-site
python3 hvac_system.py --sensor-file sensors.json --iterations 1 --off-delay-seconds 0
```

`--off-delay-seconds 0` means immediate shutoff when no occupancy is detected.

## Simulating occupancy changes

Update `occupied` values inside `sensors.json` and rerun the command to simulate real sensor updates.

## Run test cases in terminal

```bash
cd /Users/drewhawley/academic-energy-site
python3 -m unittest discover -s tests -p "test_*.py" -v
```

## Display test cases on localhost

```bash
cd /Users/drewhawley/academic-energy-site
python3 test_dashboard.py --port 8080
```

Then open `http://127.0.0.1:8080` in your browser. Refreshing the page reruns the tests and updates the report.

## Run academic building HVAC localhost

```bash
cd /Users/drewhawley/academic-energy-site
python3 academic_hvac_localhost.py --port 8090
```

Then open `http://127.0.0.1:8090` in your browser.

API endpoints:

- `GET /api/status`: Returns current tracked statuses for all buildings.
- `GET /api/status?building_id=Building_A`: Returns status for a single building.
- `POST /api/check-update` with JSON body `{"building_id": "Building_A"}`: Checks schedule and updates the building HVAC to `ON` or `OFF`.
- `POST /api/check-update-all`: Checks all academic buildings and updates each HVAC status.
