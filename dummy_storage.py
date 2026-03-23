"""
dummy_storage.py
Simulates the TimescaleDB/PostgreSQL database with hardcoded product recipes.
Replaces batch_plant_storage.py when no real database is available.
"""

import json
from typing import Optional, List, Dict


# Dummy recipe data — simulates what the real DB would return
# Each product maps to a list of {material_name, tank_number, quantity (litres per batch)}
DUMMY_RECIPES = {
    "Product A": [
        {"material_name": "Material A", "tank_number": 1, "quantity": 100.0},
        {"material_name": "Material B", "tank_number": 2, "quantity": 200.0},
        {"material_name": "Material C", "tank_number": 3, "quantity": 150.0},
    ],
    "Product B": [
        {"material_name": "Material A", "tank_number": 1, "quantity": 200.0},
        {"material_name": "Material B", "tank_number": 2, "quantity": 100.0},
        {"material_name": "Material C", "tank_number": 3, "quantity": 300.0},
    ],
    "Product C": [
        {"material_name": "Material A", "tank_number": 1, "quantity": 150.0},
        {"material_name": "Material B", "tank_number": 2, "quantity": 250.0},
        {"material_name": "Material C", "tank_number": 3, "quantity": 100.0},
    ],
}


def get_product_details(product_name: str) -> Optional[str]:
    """
    Returns recipe details for a product as a JSON string.
    Simulates the real DB query in batch_plant_storage.py.
    """
    recipe = DUMMY_RECIPES.get(product_name)
    if recipe is None:
        print(f"No recipe found for product: {product_name}")
        return None
    result = {
        "product_name": product_name,
        "recipe": recipe
    }
    return json.dumps(result, indent=2)
