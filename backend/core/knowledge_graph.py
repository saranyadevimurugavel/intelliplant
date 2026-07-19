"""
Knowledge Graph — in-memory NetworkX graph persisted as JSON.
Nodes: assets, documents, events, regulations, personnel
Edges: relationships with typed labels
"""
import json
import os
import logging
import networkx as nx
from typing import Optional
from datetime import datetime, timezone

from core.config import settings

logger = logging.getLogger(__name__)

# Global knowledge graph instance
kg: nx.DiGraph = nx.DiGraph()


def init_knowledge_graph():
    """Load persisted graph or create a new one."""
    global kg
    path = settings.knowledge_graph_path
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                data = json.load(f)
            kg = nx.node_link_graph(data)
            logger.info(f"Knowledge graph loaded: {kg.number_of_nodes()} nodes, {kg.number_of_edges()} edges")
        except Exception as e:
            logger.warning(f"Failed to load knowledge graph: {e}. Starting fresh.")
            kg = nx.DiGraph()
    else:
        kg = nx.DiGraph()
        _seed_demo_graph()
        logger.info("Knowledge graph initialised with demo data.")


def save_knowledge_graph():
    """Persist graph to disk."""
    path = settings.knowledge_graph_path
    with open(path, "w") as f:
        json.dump(nx.node_link_data(kg), f, default=str)


def add_entity(node_id: str, node_type: str, **attrs):
    """Add or update a node."""
    # Remove 'type' from attrs to avoid collision with our node_type field
    attrs.pop("type", None)
    kg.add_node(node_id, node_type=node_type, updated_at=datetime.now(timezone.utc).isoformat(), **attrs)
    save_knowledge_graph()


def add_relationship(source_id: str, target_id: str, relation: str, **attrs):
    """Add a directed edge between two entities."""
    kg.add_edge(source_id, target_id, relation=relation, **attrs)
    save_knowledge_graph()


def get_entity(node_id: str) -> Optional[dict]:
    if node_id in kg.nodes:
        return dict(kg.nodes[node_id])
    return None


def get_neighbors(node_id: str, relation: Optional[str] = None) -> list:
    """Get all connected nodes, optionally filtered by relation type."""
    results = []
    for _, target, data in kg.out_edges(node_id, data=True):
        if relation is None or data.get("relation") == relation:
            results.append({"node_id": target, "relation": data.get("relation"), **dict(kg.nodes[target])})
    return results


def get_asset_full_context(asset_tag: str) -> dict:
    """Get everything known about an asset from the knowledge graph."""
    if asset_tag not in kg.nodes:
        return {}

    context = {
        "asset": dict(kg.nodes[asset_tag]),
        "maintenance_records": [],
        "documents": [],
        "incidents": [],
        "regulations": [],
        "related_assets": [],
    }

    for _, target, data in kg.out_edges(asset_tag, data=True):
        relation = data.get("relation", "")
        node_data = {"node_id": target, **dict(kg.nodes.get(target, {}))}
        if relation == "has_work_order":
            context["maintenance_records"].append(node_data)
        elif relation == "documented_in":
            context["documents"].append(node_data)
        elif relation == "involved_in_incident":
            context["incidents"].append(node_data)
        elif relation == "governed_by":
            context["regulations"].append(node_data)
        elif relation == "connected_to":
            context["related_assets"].append(node_data)

    return context


def search_entities(query: str, node_type: Optional[str] = None) -> list:
    """Simple text search across node attributes."""
    results = []
    query_lower = query.lower()
    for node_id, attrs in kg.nodes(data=True):
        if node_type and attrs.get("node_type") != node_type:
            continue
        searchable = " ".join(str(v) for v in attrs.values()).lower()
        if query_lower in searchable:
            results.append({"node_id": node_id, **attrs})
    return results[:20]


def get_graph_stats() -> dict:
    return {
        "total_nodes": kg.number_of_nodes(),
        "total_edges": kg.number_of_edges(),
        "node_types": _count_by_type(),
    }


def _count_by_type() -> dict:
    counts = {}
    for _, attrs in kg.nodes(data=True):
        t = attrs.get("node_type", "unknown")
        counts[t] = counts.get(t, 0) + 1
    return counts


def _seed_demo_graph():
    """Seed a minimal demo knowledge graph with realistic industrial data."""
    # Assets
    add_entity("PUMP-P101", "asset", name="Crude Feed Pump P-101", area="CDU-Unit1",
               manufacturer="KSB", model="Etanorm 65-200", install_year=2015,
               criticality="high", status="operational")
    add_entity("PUMP-P102", "asset", name="Reflux Pump P-102", area="CDU-Unit1",
               manufacturer="KSB", model="Etanorm 50-160", install_year=2016,
               criticality="high", status="operational")
    add_entity("HX-E201", "asset", name="Feed Pre-Heater E-201", area="CDU-Unit1",
               manufacturer="Alfa Laval", model="AlfaNova 76", install_year=2015,
               criticality="medium", status="operational")
    add_entity("PSV-201", "asset", name="Pressure Safety Valve PSV-201", area="CDU-Unit1",
               manufacturer="Emerson", model="Series 800", install_year=2017,
               criticality="critical", status="operational")
    add_entity("COMP-C301", "asset", name="Offgas Compressor C-301", area="GasPlant-Unit3",
               manufacturer="Siemens", model="STC-S", install_year=2018,
               criticality="critical", status="under_maintenance")

    # Documents
    add_entity("DOC-001", "document", name="P-101 OEM Maintenance Manual Rev 4",
               doc_type="pdf", category="engineering", filename="p101_oem_manual_r4.pdf")
    add_entity("DOC-002", "document", name="CDU Unit 1 Operating Procedure SOP-CDU-001 Rev 7",
               doc_type="pdf", category="operating_procedure", filename="sop_cdu_001_r7.pdf")
    add_entity("DOC-003", "document", name="OISD-STD-116 Process Safety Management",
               doc_type="pdf", category="regulation", filename="oisd_116.pdf")
    add_entity("DOC-004", "document", name="Inspection Report IR-2024-0341",
               doc_type="pdf", category="inspection", filename="ir_2024_0341.pdf")
    add_entity("DOC-005", "document", name="Incident Report INC-2023-0087",
               doc_type="pdf", category="incident", filename="inc_2023_0087.pdf")

    # Work Orders
    add_entity("WO-4521", "work_order", work_order_id="WO-4521", work_type="corrective",
               description="Mechanical seal replacement on P-101", status="completed",
               completed_date="2024-03-15", technician="R. Sharma")
    add_entity("WO-4688", "work_order", work_order_id="WO-4688", work_type="preventive",
               description="Annual inspection and bearing replacement on C-301",
               status="in_progress", technician="A. Kumar")
    add_entity("WO-4702", "work_order", work_order_id="WO-4702", work_type="inspection",
               description="PSV-201 bench test and certification", status="scheduled",
               scheduled_date="2024-08-01")

    # Regulations
    add_entity("REG-OISD-116", "regulation", name="OISD-STD-116",
               title="Process Safety Management", authority="OISD", applicable_areas="all")
    add_entity("REG-PESO-2022", "regulation", name="PESO Pressure Vessel Regulations 2022",
               title="Static & Mobile Pressure Vessels Rules", authority="PESO")
    add_entity("REG-FACTORIES-ACT", "regulation", name="Factories Act 1948",
               title="Factories Act 1948 - Schedule", authority="Ministry of Labour")

    # Incidents
    add_entity("INC-2023-0087", "incident", type="mechanical_failure",
               description="P-101 mechanical seal failure causing process leak",
               severity="major", root_cause="Seal face wear due to dry running",
               corrective_action="Seal replaced, flush plan upgraded to Plan 23")

    # Personnel
    add_entity("PERSON-RS", "person", name="R. Sharma", role="Maintenance Technician", area="CDU")
    add_entity("PERSON-AK", "person", name="A. Kumar", role="Senior Technician", area="GasPlant")

    # Relationships
    add_relationship("PUMP-P101", "WO-4521", "has_work_order")
    add_relationship("PUMP-P101", "DOC-001", "documented_in")
    add_relationship("PUMP-P101", "DOC-002", "referenced_in")
    add_relationship("PUMP-P101", "INC-2023-0087", "involved_in_incident")
    add_relationship("PUMP-P101", "REG-OISD-116", "governed_by")
    add_relationship("PUMP-P101", "HX-E201", "connected_to")
    add_relationship("PUMP-P102", "HX-E201", "connected_to")
    add_relationship("PSV-201", "WO-4702", "has_work_order")
    add_relationship("PSV-201", "REG-PESO-2022", "governed_by")
    add_relationship("COMP-C301", "WO-4688", "has_work_order")
    add_relationship("WO-4521", "PERSON-RS", "performed_by")
    add_relationship("WO-4688", "PERSON-AK", "performed_by")
    add_relationship("INC-2023-0087", "DOC-005", "documented_in")
    add_relationship("DOC-004", "PUMP-P101", "inspects")
    add_relationship("DOC-003", "REG-OISD-116", "is_standard")

    logger.info("Demo knowledge graph seeded.")
