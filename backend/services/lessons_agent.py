"""Lessons Learned & Failure Intelligence Engine — using Groq."""
import logging
from typing import List, Optional
from datetime import datetime, timezone
from groq import Groq

from core.config import settings

logger = logging.getLogger(__name__)

DEMO_LESSONS = [
    {"id": "LL-001", "incident_type": "mechanical_failure", "asset_tag": "PUMP-P101", "title": "Mechanical Seal Failure Due to Dry Running — CDU Feed Pump", "description": "P-101 mechanical seal failed after 3 hours of dry running during crude feed switchover. 15 litres crude oil released.", "root_cause": "API Plan 11 flush line orifice blocked by crude wax deposits. Seal starved of flush fluid.", "corrective_actions": "Seal replaced. Flush plan upgraded to API Plan 23. Orifice enlarged 3mm→5mm.", "preventive_actions": "Add flush flow indicator to all critical pump seals. Include in daily rounds checklist.", "severity": "major", "recurrence_count": 2, "pattern_tags": ["mechanical_seal", "dry_running", "flush_failure", "crude_service"], "date": "2024-03-15", "area": "CDU-Unit1"},
    {"id": "LL-002", "incident_type": "near_miss", "asset_tag": "COMP-C301", "title": "Near-Miss: Compressor Vibration Alert Ignored — Bearing Failure Averted", "description": "C-301 vibration alarm silenced without investigation. Vibration reached trip level 6 hours later causing emergency shutdown.", "root_cause": "Vibration alarm classified as 'nuisance alarm'. Operators conditioned to silence it.", "corrective_actions": "Emergency bearing replacement. Alarm reclassified as priority 1.", "preventive_actions": "Monthly review of silenced alarms. Vibration trend monitoring added to daily rounds.", "severity": "high", "recurrence_count": 1, "pattern_tags": ["vibration", "alarm_management", "bearing_failure", "compressor"], "date": "2023-11-22", "area": "GasPlant-Unit3"},
    {"id": "LL-003", "incident_type": "quality_deviation", "asset_tag": "HX-E201", "title": "Heat Exchanger Fouling Causing Product Quality Deviation", "description": "CDU overhead product failed specification for 3 days due to E-201 fouling.", "root_cause": "E-201 cleaning interval extended 6→12 months without risk assessment.", "corrective_actions": "E-201 cleaned. Specification restored in 24 hours.", "preventive_actions": "Restore 6-month cleaning cycle. Add dP monitoring. MOC required for interval changes.", "severity": "major", "recurrence_count": 1, "pattern_tags": ["heat_exchanger", "fouling", "product_quality", "maintenance_interval"], "date": "2023-08-07", "area": "CDU-Unit1"},
    {"id": "LL-004", "incident_type": "safety", "asset_tag": "PSV-201", "title": "PSV Failed to Lift at Set Pressure During Bench Test", "description": "PSV-201 failed to lift at 23.5 barg set pressure — actual lift at 28.1 barg (19% high). 26 months in service without testing.", "root_cause": "Corrosion buildup on disc and seat. Exceeded maximum service interval in chloride service.", "corrective_actions": "PSV replaced. Failed unit sent for refurbishment.", "preventive_actions": "Reduce testing interval to 18 months for PSVs in chloride service. Add PSV test status to compliance dashboard.", "severity": "critical", "recurrence_count": 1, "pattern_tags": ["psv", "safety_valve", "corrosion", "compliance", "pressure_relief"], "date": "2022-07-20", "area": "CDU-Unit1"},
]

DEMO_WARNINGS = [
    {"id": "WARN-001", "trigger": "C-301 vibration elevated trend", "related_lesson": "LL-002", "warning_title": "⚠️ Vibration Pattern Matches Historical Bearing Failure on C-301", "warning_detail": "Current C-301 vibration trend (drive-end, 7.2 mm/s rising) matches pattern preceding November 2023 bearing failure (LL-002). Alarm was silenced 6 hours before emergency shutdown.", "severity": "high", "asset_tag": "COMP-C301", "recommended_action": "Do not silence vibration alarm. Initiate urgent inspection of drive-end bearing.", "generated_at": datetime.now(timezone.utc).isoformat()},
    {"id": "WARN-002", "trigger": "PSV-201 certification overdue", "related_lesson": "LL-004", "warning_title": "⚠️ PSV Certification Overdue — Previous Failure at Similar Interval", "warning_detail": "PSV-201 exceeded certification interval. LL-004 documented PSV in same service failing to lift at set pressure after 26 months. Current: 24+ months in chloride service.", "severity": "critical", "asset_tag": "PSV-201", "recommended_action": "Escalate for immediate bench test scheduling.", "generated_at": datetime.now(timezone.utc).isoformat()},
]


def get_lessons(incident_type=None, asset_tag=None, severity=None, tag=None):
    lessons = DEMO_LESSONS
    if incident_type:
        lessons = [l for l in lessons if l["incident_type"] == incident_type]
    if asset_tag:
        lessons = [l for l in lessons if l["asset_tag"].upper() == asset_tag.upper()]
    if severity:
        lessons = [l for l in lessons if l["severity"] == severity]
    if tag:
        lessons = [l for l in lessons if tag.lower() in [t.lower() for t in l.get("pattern_tags", [])]]
    return lessons


def get_proactive_warnings():
    return DEMO_WARNINGS


async def analyze_patterns(asset_tag=None):
    """Use Groq to identify systemic patterns across lessons learned."""
    lessons = get_lessons(asset_tag=asset_tag) if asset_tag else DEMO_LESSONS

    lessons_text = "\n\n".join([
        f"ID: {l['id']} | Type: {l['incident_type']} | Asset: {l['asset_tag']}\n"
        f"Title: {l['title']}\nRoot Cause: {l['root_cause']}\nTags: {', '.join(l['pattern_tags'])}"
        for l in lessons
    ])

    prompt = f"""You are a Reliability Engineering expert analysing industrial incident data.

LESSONS LEARNED:
{lessons_text}

Identify:
1. **Systemic Patterns** — recurring failure modes across incidents
2. **High-Risk Areas** — equipment or practices with disproportionate risk
3. **Organisational Factors** — management system or culture weaknesses
4. **Priority Recommendations** — top 3 actions to reduce overall risk
5. **Knowledge Gaps** — areas needing more investigation

Reference specific incident IDs in your analysis."""

    try:
        client = Groq(api_key=settings.groq_api_key)
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": "You are a senior Reliability and Safety Engineer in Indian petroleum refining."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=1200,
        )
        analysis = response.choices[0].message.content
    except Exception as e:
        logger.error(f"Groq pattern analysis failed: {e}")
        analysis = f"Pattern analysis unavailable — check Groq API key. ({len(lessons)} lessons reviewed)"

    return {
        "lessons_analyzed": len(lessons),
        "pattern_analysis": analysis,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
