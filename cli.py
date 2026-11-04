#!/usr/bin/env python3

from py_uconnect import Client
from py_uconnect.brands import BRANDS
from sys import argv, exit


if len(argv) < 4:
    print(
        "Incorrect arguments. Pass brand, login, password and optionally pin as arguments."
    )
    print("Usage: cli.py BRAND LOGIN PASSWORD [PIN] [--dev]")
    exit(1)

brand, login, password = argv[1], argv[2], argv[3]
pin = argv[4] if len(argv) > 4 and argv[4] != "--dev" else ""
dev_mode = "--dev" in argv[4:]

brand = BRANDS.get(brand, None)
if brand is None:
    print(
        f"Incorrect brand. Possible values are: {', '.join([x for x in BRANDS.keys()])}"
    )
    exit(1)

c = Client(login, password, pin, brand=brand, dev_mode=dev_mode)
c.refresh()

if pin:
    for veh_vin in c.get_vehicles():
        try:
            c.force_refresh(veh_vin)
        except Exception as err:
            print(f"Deep refresh failed for {veh_vin}: {err}")
    c.refresh()

v = c.get_vehicles()

for veh in v.values():
    print(veh.to_json(indent=2))
