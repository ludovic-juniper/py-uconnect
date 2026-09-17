#!/usr/bin/env python3
"""
CLI script to set the EV charging level (1 to 5) using command-line arguments.

Usage:
    python charge_level_cli.py USERID PWD PIN LEVEL [BRAND]

Example:
    python charge_level_cli.py your_email@example.com your_password your_pin 5 JEEP_EU

Where:
    USERID - Your Uconnect account email
    PWD    - Your Uconnect account password
    PIN    - Your vehicle PIN
    LEVEL  - Charging level (1 to 5)
    BRAND  - (Optional) Brand code, defaults to JEEP_EU
"""

import sys
import time

import requests

from py_uconnect import Client
from py_uconnect.api import CHARGING_LEVELS
from py_uconnect.brands import BRANDS


MAX_ATTEMPTS = 4
RETRY_BACKOFF_SECONDS = 5


def main():
    if len(sys.argv) < 5:
        print("Usage: python charge_level_cli.py USERID PWD PIN LEVEL [BRAND]")
        print("Example: python charge_level_cli.py email@example.com password 1234 5 JEEP_EU")
        sys.exit(1)

    userid = sys.argv[1]
    pwd = sys.argv[2]
    pin = sys.argv[3]

    try:
        level = int(sys.argv[4])
    except ValueError:
        print(f"Error: LEVEL must be an integer between 1 and 5, got '{sys.argv[4]}'")
        sys.exit(1)

    if level < 1 or level > 5:
        print(f"Error: LEVEL must be between 1 and 5, got {level}")
        sys.exit(1)

    brand_name = sys.argv[5] if len(sys.argv) > 5 else "JEEP_EU"

    brand = BRANDS.get(brand_name)
    if brand is None:
        print(f"Error: Unknown brand '{brand_name}'")
        print(f"Available brands: {', '.join(BRANDS.keys())}")
        sys.exit(1)

    charging_level = CHARGING_LEVELS[level - 1]

    print(f"Connecting as {userid} with brand {brand_name}...")
    print(f"Setting charging level to {level} ({charging_level.name})")

    client = Client(userid, pwd, pin=pin, brand=brand)

    print("Refreshing vehicle data...")
    client.refresh()

    vehicles = client.get_vehicles()
    if not vehicles:
        print("No vehicles found")
        sys.exit(1)

    vehicle = list(vehicles.values())[0]
    print(f"Found vehicle: {vehicle.nickname} ({vehicle.vin})")

    current_pref = getattr(vehicle, "charging_level_preference", None)
    print(f"Current charging level preference: {current_pref}")

    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            print(f"Sending command (attempt {attempt}/{MAX_ATTEMPTS}) and waiting for confirmation...")
            success = client.set_charging_level_verify(vehicle.vin, charging_level)
            if success:
                print("Charging level updated successfully.")
                sys.exit(0)

            print("Charging level update did not complete successfully.")
            sys.exit(1)

        except requests.exceptions.HTTPError as e:
            last_error = e
            status = e.response.status_code if e.response is not None else None
            if status is not None and 500 <= status < 600 and attempt < MAX_ATTEMPTS:
                print(f"Server returned HTTP {status}; retrying in {RETRY_BACKOFF_SECONDS}s...")
                time.sleep(RETRY_BACKOFF_SECONDS)
                continue
            print(f"Error setting charging level: {e}")
            sys.exit(1)

        except Exception as e:
            print(f"Error setting charging level: {e}")
            sys.exit(1)

    print(f"Error setting charging level after {MAX_ATTEMPTS} attempts: {last_error}")
    sys.exit(1)


if __name__ == '__main__':
    main()
