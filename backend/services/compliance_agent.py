"""Compliance Intelligence Agent — using Groq."""
import logging
from typing import List, Optional
from datetime import datetime, timezone
from groq import Groq

from core.config import settings

logger = logging.getLogger(__name__)

DEMO_COMPLIANCE_GAPS = [
    {"id": "GAP-001", "regulation": "OISD-STD-116", "clause": "Section 4.3.2", "requirement": "Written operating procedures shall be established for all process units covering startup, normal operations, emergency shutdown, and temporary operations.", "current_state": "SOP-CDU-001 Rev 7 covers normal operations. Emergency shutdown procedure ESP-CDU-001 last reviewed 2019.", "gap_description": "Emergency shutdown procedure not reviewed within 3-year cycle (now 5 years old). Does not reflect 2022 DCS upgrade.", "severity": "major", "status": "open", "corrective_action": "Review and update ESP-CDU-001 to reflect current DCS configuration.", "due_date": "2024-09-30", "area": "CDU-Unit1"},
    {"id": "GAP-002", "regulation": "PESO", "clause": "Static & Mobile Pressure Vessels Rules – Rule 18", "requirement": "All pressure safety valves shall be bench tested and certified every 2 years.", "current_state": "PSV-201 last certified 2022-07-20.", "gap_description": "PSV-201 certification overdue. No completed WO on record.", "severity": "critical", "status": "open", "corrective_action": "Issue emergency WO for PSV-201 bench test immediately.", "due_date": "2024-07-31", "area": "CDU-Unit1"},
    {"id": "GAP-003", "regulation": "Factories Act 1948", "clause": "Section 41-B", "requirement": "Maintain up-to-date safety data sheets for all hazardous chemicals on site.", "current_state": "Crude oil SDS is 2018 version.", "gap_description": "Crude oil SDS 6 years old — does not reflect current crude slate composition.", "severity": "major", "status": "in_progress", "corrective_action": "Update crude oil SDS with current crude slate.", "due_date": "2024-08-15", "area": "Site-wide"},
    {"id": "GAP-004", "regulation": "OISD-STD-116", "clause": "Section 7.1", "requirement": "Management of Change procedure shall be followed for all process, equipment, or procedural changes.", "current_state": "DCS upgrade in 2022 completed with informal MOC only.", "gap_description": "2022 DCS upgrade lacks formal MOC documentation and HAZOP review.", "severity": "major", "status": "open", "corrective_action": "Conduct retrospective HAZOP for 2022 DCS changes. Create MOC register entry.", "due_date": "2024-10-31", "area": "CDU-Unit1"},
    {"id": "GAP-005", "regulation": "CPCB", "clause": "Air Quality Consent – Condition 12", "requirement": "Stack emission monitoring reports submitted quarterly to SPCB.", "current_state": "Q2 2024 report not yet submitted.", "gap_description": "Q2 2024 emission monitoring report overdue.", "severity": "minor", "status": "open", "corrective_action": "Complete Q2 2024 stack emission data and submit to SPCB.", "due_date": "2024-08-05", "area": "Site-wide"},
]

COMPLIANCE_HEALTH = {
    "overall_score": 67,
    "by_regulation": {
        "OISD-STD-116": {"score": 72, "open_gaps": 2, "critical": 0, "major": 2},
        "PESO": {"score": 45, "open_gaps": 1, "critical": 1, "major": 0},
        "Factories Act 1948": {"score": 80, "open_gaps": 1, "critical": 0, "major": 1},
        "CPCB": {"score": 85, "open_gaps": 1, "critical": 0, "major": 0},
    },
}


def get_compliance_gaps(regulation=None, severity=None, status=None):
    gaps = DEMO_COMPLIANCE_GAPS
    if regulation:
        gaps = [g for g in gaps if regulation.lower() in g["regulation"].lower()]
    if severity:
        gaps = [g for g in gaps if g["severity"] == severity]
    if status:
        gaps = [g for g in gaps if g["status"] == status]
    return gaps


def get_compliance_health():
    gaps = DEMO_COMPLIANCE_GAPS
    health = dict(COMPLIANCE_HEALTH)
    health["last_updated"] = datetime.now(timezone.utc).isoformat()
    health["summary"] = {
        "total_open_gaps": len([g for g in gaps if g["status"] == "open"]),
        "critical": len([g for g in gaps if g["severity"] == "critical" and g["status"] == "open"]),
        "major": len([g for g in gaps if g["severity"] == "major" and g["status"] == "open"]),
        "minor": len([g for g in gaps if g["severity"] == "minor" and g["status"] == "open"]),
    }
    return health


async def generate_audit_package(regulation: str) -> dict:
    """Generate audit evidence package using Groq."""
    relevant_gaps = get_compliance_gaps(regulation=regulation)

    gaps_text = "\n".join([
        f"- [{g['severity'].upper()}] {g['clause']}: {g['gap_description']} (Due: {g['due_date']})"
        for g in relevant_gaps
    ]) or "No gaps identified."

    prompt = f"""You are a regulatory compliance expert preparing an audit evidence package for {regulation}.

COMPLIANCE GAPS:
{gaps_text}

Generate a structured audit evidence package with:
1. **Executive Summary** — overall compliance status
2. **Compliant Areas** — what is currently in order
3. **Gap Summary** — gaps with severity ratings
4. **Evidence Required** — documents and records to compile
5. **Immediate Actions** — actions required before audit
6. **Compliance Timeline** — realistic timeline to close all gaps

Format professionally for a regulatory inspector."""

    try:
        client = Groq(api_key=settings.groq_api_key)
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": "You are a regulatory compliance expert in Indian heavy industry."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=1200,
        )
        package_text = response.choices[0].message.content
    except Exception as e:
        logger.error(f"Groq audit package failed: {e}")
        package_text = f"**Audit Package — {regulation}**\n\nGaps:\n{gaps_text}\n\n*LLM unavailable — check Groq API key.*"

    return {
        "regulation": regulation,
        "gaps_count": len(relevant_gaps),
        "critical_gaps": len([g for g in relevant_gaps if g["severity"] == "critical"]),
        "package_content": package_text,
        "gaps": relevant_gaps,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
