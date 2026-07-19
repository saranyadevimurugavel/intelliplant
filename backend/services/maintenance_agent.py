"""Maintenance Intelligence & RCA Agent — using Groq."""
import logging
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from groq import Groq

from core.config import settings
from core.knowledge_graph import get_asset_full_context

logger = logging.getLogger(__name__)

DEMO_MAINTENANCE_DATA = [
    {"asset_tag": "PUMP-P101", "asset_name": "Crude Feed Pump P-101", "work_order_id": "WO-4521", "type": "corrective", "description": "Mechanical seal replacement", "findings": "Seal faces worn due to dry running. Flush plan inadequate.", "completed_date": "2024-03-15", "technician": "R. Sharma", "downtime_hours": 8},
    {"asset_tag": "PUMP-P101", "asset_name": "Crude Feed Pump P-101", "work_order_id": "WO-4210", "type": "preventive", "description": "Bearing inspection and lubrication", "findings": "Slight bearing wear noted. Re-lubricated.", "completed_date": "2023-09-10", "technician": "A. Kumar", "downtime_hours": 2},
    {"asset_tag": "COMP-C301", "asset_name": "Offgas Compressor C-301", "work_order_id": "WO-4688", "type": "preventive", "description": "Annual inspection and bearing replacement", "findings": "In progress — vibration levels elevated on drive-end bearing.", "completed_date": None, "technician": "A. Kumar", "downtime_hours": None},
    {"asset_tag": "PSV-201", "asset_name": "Pressure Safety Valve PSV-201", "work_order_id": "WO-4702", "type": "inspection", "description": "PSV bench test and certification", "findings": "Scheduled. Last tested 2022-07-20. PESO compliance due.", "completed_date": None, "technician": None, "downtime_hours": None},
]

DEMO_RECOMMENDATIONS = [
    {"id": "REC-001", "asset_tag": "COMP-C301", "asset_name": "Offgas Compressor C-301", "priority": "high", "type": "predictive", "recommendation": "Drive-end bearing replacement recommended within 14 days.", "basis": "Vibration amplitude on drive-end bearing increased 40% over last 30 days. Pattern matches bearing fatigue failure mode in OEM manual Section 6.4.", "predicted_failure_date": (datetime.now(timezone.utc) + timedelta(days=14)).strftime("%Y-%m-%d"), "relevant_documents": ["C-301 OEM Manual Rev 2", "WO-4688"], "estimated_downtime": "6 hours"},
    {"id": "REC-002", "asset_tag": "PSV-201", "asset_name": "Pressure Safety Valve PSV-201", "priority": "critical", "type": "compliance", "recommendation": "PSV-201 bench test overdue. PESO certification expires 2024-07-31.", "basis": "Last certified 2022-07-20. PESO rules require biennial testing.", "predicted_failure_date": "2024-07-31", "relevant_documents": ["PESO Pressure Vessel Regulations 2022", "WO-4702"], "estimated_downtime": "4 hours"},
    {"id": "REC-003", "asset_tag": "PUMP-P101", "asset_name": "Crude Feed Pump P-101", "priority": "medium", "type": "preventive", "recommendation": "Schedule bearing inspection. Last inspection 10 months ago; OEM interval is 12 months.", "basis": "OEM manual recommends annual bearing inspection. Last WO (WO-4210) completed 2023-09-10.", "predicted_failure_date": (datetime.now(timezone.utc) + timedelta(days=60)).strftime("%Y-%m-%d"), "relevant_documents": ["P-101 OEM Manual Rev 4"], "estimated_downtime": "2 hours"},
]


def get_recommendations(asset_tag=None, priority=None):
    recs = DEMO_RECOMMENDATIONS
    if asset_tag:
        recs = [r for r in recs if r["asset_tag"].upper() == asset_tag.upper()]
    if priority:
        recs = [r for r in recs if r["priority"] == priority]
    return recs


def get_maintenance_history(asset_tag=None):
    records = DEMO_MAINTENANCE_DATA
    if asset_tag:
        records = [r for r in records if r["asset_tag"].upper() == asset_tag.upper()]
    return records


async def generate_rca(asset_tag: str, failure_description: str) -> dict:
    """Generate Root Cause Analysis using Groq LLaMA."""
    history = get_maintenance_history(asset_tag)
    kg_context = get_asset_full_context(asset_tag.upper())

    history_text = "\n".join([
        f"- WO {r['work_order_id']} ({r['completed_date'] or 'in progress'}): {r['description']}. Findings: {r['findings']}"
        for r in history
    ]) or "No maintenance history available."

    kg_summary = ""
    if kg_context.get("asset"):
        a = kg_context["asset"]
        kg_summary = f"Asset: {a.get('name')} | Criticality: {a.get('criticality')} | Status: {a.get('status')}"
    if kg_context.get("incidents"):
        kg_summary += f"\nPrevious incidents: {len(kg_context['incidents'])} recorded."

    prompt = f"""You are an expert Reliability Engineer performing a Root Cause Analysis.

ASSET: {asset_tag}
{kg_summary}

REPORTED FAILURE: {failure_description}

MAINTENANCE HISTORY:
{history_text}

Perform a structured RCA using the 5-Why methodology:
1. **Immediate Cause**
2. **Contributing Factors**
3. **Root Cause**
4. **Similar Historical Events**
5. **Corrective Actions**
6. **Preventive Actions**
7. **Recommended Documents to Review**"""

    try:
        client = Groq(api_key=settings.groq_api_key)
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": "You are a senior Reliability Engineer in a petroleum refinery."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=1500,
        )
        rca_text = response.choices[0].message.content
    except Exception as e:
        logger.error(f"Groq RCA failed: {e}")
        rca_text = f"**RCA for {asset_tag}**\n\nReported: {failure_description}\n\nHistory: {len(history)} work orders found.\n\n*LLM unavailable — check Groq API key.*"

    return {
        "asset_tag": asset_tag,
        "failure_description": failure_description,
        "rca_analysis": rca_text,
        "maintenance_history_count": len(history),
        "kg_context": kg_summary,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def get_maintenance_schedule():
    today = datetime.now(timezone.utc)
    return [
        {"work_order_id": "WO-4688", "asset_tag": "COMP-C301", "asset_name": "Offgas Compressor C-301", "work_type": "Annual Inspection", "status": "in_progress", "start_date": (today - timedelta(days=3)).strftime("%Y-%m-%d"), "estimated_completion": (today + timedelta(days=4)).strftime("%Y-%m-%d"), "technician": "A. Kumar", "priority": "high"},
        {"work_order_id": "WO-4702", "asset_tag": "PSV-201", "asset_name": "Pressure Safety Valve PSV-201", "work_type": "PSV Bench Test & Certification", "status": "scheduled", "start_date": (today + timedelta(days=14)).strftime("%Y-%m-%d"), "estimated_completion": (today + timedelta(days=14)).strftime("%Y-%m-%d"), "technician": "TBD", "priority": "critical"},
        {"work_order_id": "WO-4750", "asset_tag": "PUMP-P101", "asset_name": "Crude Feed Pump P-101", "work_type": "Annual Bearing Inspection", "status": "planned", "start_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"), "estimated_completion": (today + timedelta(days=60)).strftime("%Y-%m-%d"), "technician": "R. Sharma", "priority": "medium"},
    ]
