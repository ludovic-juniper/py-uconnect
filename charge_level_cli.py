#!/usr/bin/env python3
"""
CLI script to set the EV charging level (1 to 5) using command-line arguments.

Usage:
    python charge_level_cli.py USERID PWD PIN LEVEL [BRAND]

Example:
    python charge_level_cli.py your_email@example.com your_password your_pin 5 JEEP_US

Where:
    USERID - Your Uconnect account email
    PWD    - Your Uconnect account password
    PIN    - Your vehicle PIN
    LEVEL  - Charging level (1 to 5)
    BRAND  - (Optional) Brand code. When omitted, the region is detected from the
             vehicle's VIN: North American VINs use JEEP_US, others use JEEP_EU.
"""

import sys
import time

import requests

from py_uconnect import Client
from py_uconnect.api import CHARGING_LEVELS
from py_uconnect.brands import BRANDS


MAX_ATTEMPTS = 4
RETRY_BACKOFF_SECONDS = 5

# WMI (first VIN digit) -> North America. 1, 4, 5 are US WMI codes.
NA_WMI_DIGITS = ("1", "4", "5")


def brand_for_vin(vin: str) -> str:
    """Pick a Jeep brand code based on the vehicle's region (VIN WMI)."""

    if vin and vin[0] in NA_WMI_DIGITS:
        return "JEEP_US"
    return "JEEP_EU"


def main():
    if len(sys.argv) < 5:
        print("Usage: python charge_level_cli.py USERID PWD PIN LEVEL [BRAND]")
        print("Example: python charge_level_cli.py email@example.com password 1234 5 JEEP_US")
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

    explicit_brand = sys.argv[5] if len(sys.argv) > 5 else None

    charging_level = CHARGING_LEVELS[level - 1]

    brand_name = explicit_brand
    if brand_name is not None:
        if BRANDS.get(brand_name) is None:
            print(f"Error: Unknown brand '{brand_name}'")
            print(f"Available brands: {', '.join(BRANDS.keys())}")
            sys.exit(1)

    client = Client(userid, pwd, pin=pin, brand=BRANDS[brand_name or "JEEP_US"])
    print(f"Connecting as {userid} with brand {brand_name or 'JEEP_US'}...")
    print(f"Setting charging level to {level} ({charging_level.name})")

    print("Refreshing vehicle data...")
    client.refresh()

    vehicles = client.get_vehicles()
    if not vehicles:
        print("No vehicles found")
        sys.exit(1)

    vehicle = list(vehicles.values())[0]
    print(f"Found vehicle: {vehicle.nickname} ({vehicle.vin})")

    # If no brand was given, make sure we're on the region matching the VIN.
    detected = brand_for_vin(vehicle.vin)
    if explicit_brand is None and detected != client.api.brand.name:
        print(f"Vehicle VIN {vehicle.vin} indicates region '{detected}'; switching brand and refreshing...")
        client = Client(userid, pwd, pin=pin, brand=BRANDS[detected])
        client.refresh()
        vehicles = client.get_vehicles()
        if not vehicles:
            print("No vehicles found after switching region")
            sys.exit(1)
        vehicle = vehicles[vehicle.vin]

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
