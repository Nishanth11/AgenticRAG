"""
main.py
Maintenance-aware production assistant using local Ollama (mistral) + Chroma RAG.
Manual tool orchestration — avoids tool-calling protocol incompatibilities with Mistral.
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

from tools import (
    material_availability_sync,
    machine_states_sync,
    check_maintenance_schedule_tool,
    check_calibration_status_tool,
    check_equipment_reliability_tool,
)
from dummy_storage import get_product_details

load_dotenv()


class ProductionAssistantResponse(BaseModel):
    decision: str                                      # YES, NO, or CONDITIONAL
    reasoning: str
    sufficient_materials: bool
    machine_states: Dict[str, str]
    material_availability: Dict[str, float]
    maintenance_conflicts: Optional[List[Dict]] = []
    calibration_issues: Optional[List[Dict]] = []
    reliability_concerns: Optional[List[Dict]] = []
    recommendations: Optional[List[str]] = []
    tools_used: List[str]


llm = ChatOllama(model="mistral")


def extract_json_from_response(text: str) -> dict:
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        return json.loads(json_match.group())
    raise ValueError("No JSON object found in LLM response")


def extract_product_name(query: str) -> Optional[str]:
    match = re.search(r'product\s+([A-Za-z])', query, re.IGNORECASE)
    return f"Product {match.group(1).upper()}" if match else None


def extract_date(query: str) -> Optional[str]:
    # Try ISO format: 2026-08-16
    match = re.search(r'\d{4}-\d{2}-\d{2}', query)
    if match:
        return match.group()
    # Try written format: August 16, 2026
    match = re.search(
        r'(January|February|March|April|May|June|July|August|September|October|November|December)'
        r'\s+\d{1,2},?\s+\d{4}',
        query, re.IGNORECASE
    )
    if match:
        for fmt in ("%B %d, %Y", "%B %d %Y"):
            try:
                return datetime.strptime(match.group(), fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
    return None


def run_assessment(query: str) -> ProductionAssistantResponse:
    product_name = extract_product_name(query) or "Product A"
    date_str = extract_date(query) or datetime.now().strftime("%Y-%m-%d")
    rag_input = f"{product_name}, {date_str}"

    # --- Call all tools to gather data ---
    materials = material_availability_sync()
    machines = machine_states_sync()
    recipe = get_product_details(product_name) or json.dumps({"error": "Product not found"})
    maintenance = check_maintenance_schedule_tool.func(rag_input)
    calibration = check_calibration_status_tool.func(rag_input)
    reliability = check_equipment_reliability_tool.func("")

    system_prompt = """\
You are an Advanced Batch Plant Production Assistant.

You will receive real-time plant data AND maintenance/calibration intelligence gathered from documents.
Your job is to synthesize all of this into a single production feasibility decision.

DECISION RULES:
- YES: All checks pass — materials sufficient, machines operational, no maintenance conflicts, calibrations valid
- NO: A critical blocker exists — list the specific reasons
- CONDITIONAL: Production is possible only with constraints or after specific actions

PRODUCT-SPECIFIC RULES:
- Product A: Cannot be produced within 24 hours after reactor maintenance
- Product A: Requires ALL instruments to be within calibration
- ALL Products: Equipment health scores must be above minimum thresholds
- ALL Products: Cannot proceed if critical spare parts are at zero

IMPORTANT: Respond with ONLY valid JSON — no explanation, no markdown, no extra text.

Required JSON format:
{
  "decision": "YES or NO or CONDITIONAL",
  "reasoning": "detailed explanation with specific numbers and dates",
  "sufficient_materials": true or false,
  "machine_states": {"mixer_state": "...", "reactor_state": "...", "filler_state": "..."},
  "material_availability": {"tank1_material_level": 0.0, "tank2_material_level": 0.0, "tank3_material_level": 0.0},
  "maintenance_conflicts": [],
  "calibration_issues": [],
  "reliability_concerns": [],
  "recommendations": [],
  "tools_used": ["get_material_availability", "get_machine_states", "get_product_details",
                 "check_maintenance_schedule", "check_calibration_status", "check_equipment_reliability"]
}"""

    human_message = f"""\
Query: {query}

Product: {product_name}
Production Date: {date_str}

--- REAL-TIME DATA ---

Material Availability (litres):
{materials}

Machine States:
{machines}

Product Recipe (litres per batch):
{recipe}

--- MAINTENANCE INTELLIGENCE (from RAG documents) ---

Maintenance Schedule Check:
{maintenance}

Calibration Status:
{calibration}

Equipment Reliability & Spare Parts:
{reliability}

---
Analyze all the above and respond with JSON only."""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_message),
    ])

    json_data = extract_json_from_response(response.content)

    # Fill missing fields from already-collected tool data so Pydantic never fails
    # on partial responses (e.g. for non-production queries like "any maintenance planned?")
    if "machine_states" not in json_data:
        json_data["machine_states"] = json.loads(machines)
    if "material_availability" not in json_data:
        json_data["material_availability"] = json.loads(materials)
    if "sufficient_materials" not in json_data:
        json_data["sufficient_materials"] = True
    if "tools_used" not in json_data:
        json_data["tools_used"] = [
            "get_material_availability", "get_machine_states", "get_product_details",
            "check_maintenance_schedule", "check_calibration_status", "check_equipment_reliability",
        ]

    return ProductionAssistantResponse(**json_data)


def _print_section(title: str, items: Optional[list], prefix: str = "  - "):
    if items:
        print(f"\n{title}")
        for item in items:
            print(f"{prefix}{item}")


def print_assessment(result: ProductionAssistantResponse):
    icons = {"YES": "OK", "NO": "BLOCKED", "CONDITIONAL": "WARNING"}
    print("\n" + "=" * 70)
    print("PRODUCTION FEASIBILITY ASSESSMENT")
    print("=" * 70)
    print(f"\n[{icons.get(result.decision, '?')}] DECISION: {result.decision}")
    print(f"\nREASONING:\n{result.reasoning}")

    print(f"\nMATERIAL AVAILABILITY (sufficient={result.sufficient_materials}):")
    for tank, level in result.material_availability.items():
        print(f"  {tank}: {level:,.2f} L")

    print("\nMACHINE STATES:")
    for machine, state in result.machine_states.items():
        ok = state.lower() not in ["fault", "error", "unplanned_downtime"]
        print(f"  [{'OK' if ok else 'FAULT'}] {machine}: {state}")

    _print_section("MAINTENANCE CONFLICTS:", result.maintenance_conflicts)
    _print_section("CALIBRATION ISSUES:", result.calibration_issues)
    _print_section("RELIABILITY CONCERNS:", result.reliability_concerns)
    _print_section("RECOMMENDATIONS:", result.recommendations, prefix="  -> ")

    print(f"\nTools used: {', '.join(result.tools_used)}")
    print("=" * 70)


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("BATCH PLANT PRODUCTION ASSISTANT (Ollama + RAG)")
    print("=" * 70)
    print("\nExample queries:")
    print("  - Can we produce 50 batches of Product A starting August 20, 2026?")
    print("  - Is it safe to start Product A production on August 16?")
    print("  - Check if we can run 30 batches of Product B today")
    print()

    query = input("Enter your production request: ")

    try:
        print("\nAnalyzing... (loading RAG + calling tools + querying Mistral)\n")
        result = run_assessment(query)
        print_assessment(result)
    except Exception as e:
        print(f"\nError: {e}")
