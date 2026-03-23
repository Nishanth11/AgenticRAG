"""
dummy_opc_ua.py
Simulates the OPC UA batch plant server with hardcoded dummy data.
Replaces batch_plant_functions.py when no real OPC UA server is available.
"""

import json
import asyncio
from typing import Dict


# Dummy sensor data — simulates what the real OPC UA server would return
DUMMY_TANK_LEVELS = {
    "tank1_material_level": 8000.0,   # litres of Material A
    "tank2_material_level": 13032.0,  # litres of Material B
    "tank3_material_level": 18947.0,  # litres of Material C
}

DUMMY_MACHINE_STATES = {
    "mixer_state": "running",
    "reactor_state": "idle",
    "filler_state": "running",
}


async def get_material_availability() -> str:
    """Returns dummy tank levels as a JSON string."""
    return json.dumps(DUMMY_TANK_LEVELS, indent=2)


async def get_machine_states() -> str:
    """Returns dummy machine states as a JSON string."""
    return json.dumps(DUMMY_MACHINE_STATES, indent=2)


async def main():
    print("Material Availability:")
    print(await get_material_availability())
    print("\nMachine States:")
    print(await get_machine_states())


if __name__ == "__main__":
    asyncio.run(main())
