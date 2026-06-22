#!/usr/bin/env python3
"""
CLI script to get charge schedules using command-line arguments.

Usage:
    python charge_schedules_cli.py USERID PWD PIN [BRAND]

Example:
    python charge_schedules_cli.py your_email@example.com your_password your_pin JEEP_EU

Where:
    USERID - Your Uconnect account email
    PWD    - Your Uconnect account password
    PIN    - Your vehicle PIN
    BRAND  - (Optional) Brand code, defaults to JEEP_EU
"""

import sys
import json
from py_uconnect import Client
from py_uconnect.brands import BRANDS


def main():
    # Check command-line arguments
    if len(sys.argv) < 4:
        print("Usage: python charge_schedules_cli.py USERID PWD PIN [BRAND]")
        print("Example: python charge_schedules_cli.py email@example.com password 1234 JEEP_EU")
        sys.exit(1)

    # Parse arguments
    userid = sys.argv[1]
    pwd = sys.argv[2]
    pin = sys.argv[3]
    brand_name = sys.argv[4] if len(sys.argv) > 4 else "JEEP_EU"

    # Get brand
    brand = BRANDS.get(brand_name)
    if brand is None:
        print(f"Error: Unknown brand '{brand_name}'")
        print(f"Available brands: {', '.join(BRANDS.keys())}")
        sys.exit(1)

    print(f"Connecting as {userid} with brand {brand_name}...")

    # Create client
    client = Client(userid, pwd, pin=pin, brand=brand)

    # Refresh vehicle data
    print("Refreshing vehicle data...")
    client.refresh()

    # Get vehicles
    vehicles = client.get_vehicles()
    if not vehicles:
        print("No vehicles found")
        sys.exit(1)

    vehicle = list(vehicles.values())[0]
    print(f"Found vehicle: {vehicle.nickname} ({vehicle.vin})")

    # Get charge schedules
    try:
        schedules = client.get_charge_schedules(vehicle.vin)
        print("\nCharge schedules:")
        print(json.dumps(schedules, indent=2))

        # Extract and display the actual schedules
        if 'schedules' in schedules:
            print(f"\nFound {len(schedules['schedules'])} schedules:")
            for i, schedule in enumerate(schedules['schedules']):
                print(f"\nSchedule {i+1}:")
                print(f"  Type: {schedule.get('scheduleType', 'Unknown')}")
                print(f"  Start: {schedule.get('startTime', 'N/A')}")
                print(f"  End: {schedule.get('endTime', 'N/A')}")
                print(f"  Charge to full: {schedule.get('chargeToFull', False)}")
                print(f"  Enabled: {schedule.get('enableScheduleType', False)}")
                print(f"  Repeat: {schedule.get('repeatSchedule', False)}")

                # Show days
                days = schedule.get('scheduledDays', {})
                active_days = [day for day, enabled in days.items() if enabled]
                print(f"  Active days: {', '.join(active_days) if active_days else 'None'}")

    except Exception as e:
        print(f"Error getting charge schedules: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
