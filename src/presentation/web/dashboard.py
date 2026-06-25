from __future__ import annotations

import os
from io import BytesIO
from typing import Any, Dict, List, Optional
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import streamlit as st
import httpx
import plotly.graph_objects as go

# Initialize API client
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

class DeadlockAPIClient:

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url

    def get_state(self) -> Dict[str, Any]:
        response = httpx.get(f"{self.base_url}/api/simulation/state")
        response.raise_for_status()
        return response.json()

    def create_process(self, pid: str, state: str) -> None:
        response = httpx.post(
            f"{self.base_url}/api/simulation/process",
            json={"pid": pid, "state": state},
        )
        response.raise_for_status()

    def delete_process(self, pid: str) -> None:
        response = httpx.delete(f"{self.base_url}/api/simulation/process/{pid}")
        response.raise_for_status()

    def update_process_state(self, pid: str, state: str) -> None:
        response = httpx.put(
            f"{self.base_url}/api/simulation/process/{pid}/state",
            json={"state": state},
        )
        response.raise_for_status()

    def create_resource(self, rid: str, total_instances: int) -> None:
        response = httpx.post(
            f"{self.base_url}/api/simulation/resource",
            json={"rid": rid, "total_instances": total_instances},
        )
        response.raise_for_status()

    def delete_resource(self, rid: str) -> None:
        response = httpx.delete(f"{self.base_url}/api/simulation/resource/{rid}")
        response.raise_for_status()

    def update_resource_instances(self, rid: str, total_instances: int) -> None:
        response = httpx.put(
            f"{self.base_url}/api/simulation/resource/{rid}",
            json={"total_instances": total_instances},
        )
        response.raise_for_status()

    def release_one_instance(self, rid: str) -> None:
        response = httpx.post(
            f"{self.base_url}/api/simulation/resource/release-one?rid={rid}"
        )
        response.raise_for_status()

    def allocate(self, rid: str, pid: str) -> None:
        response = httpx.post(
            f"{self.base_url}/api/simulation/allocate",
            json={"rid": rid, "pid": pid},
        )
        response.raise_for_status()

    def request(self, pid: str, rid: str) -> None:
        response = httpx.post(
            f"{self.base_url}/api/simulation/request",
            json={"pid": pid, "rid": rid},
        )
        response.raise_for_status()

    def release(self, rid: str, pid: str) -> None:
        response = httpx.post(
            f"{self.base_url}/api/simulation/release",
            json={"rid": rid, "pid": pid},
        )
        response.raise_for_status()

    def reset(self) -> None:
        response = httpx.post(f"{self.base_url}/api/simulation/reset")
        response.raise_for_status()

    def evaluate_bankers(
        self,
        allocation: List[List[int]],
        maximum: List[List[int]],
        available: List[int],
        process_names: List[str],
    ) -> Dict[str, Any]:
        response = httpx.post(
            f"{self.base_url}/api/bankers/evaluate",
            json={
                "allocation": allocation,
                "maximum": maximum,
                "available": available,
                "process_names": process_names,
            },
        )
        response.raise_for_status()
        return response.json()

    def explain_deadlock(
        self,
        cycle: List[str],
        processes: List[str],
        resources: List[str],
        banker_summary: Optional[str] = None,
    ) -> Dict[str, Any]:
        response = httpx.post(
            f"{self.base_url}/api/ai/explain",
            json={
                "deadlock_cycle": cycle,
                "processes": processes,
                "resources": resources,
                "banker_summary": banker_summary,
            },
        )
        response.raise_for_status()
        return response.json()

    def download_report(self, payload: Dict[str, Any]) -> bytes:
        response = httpx.post(f"{self.base_url}/api/ai/report", json=payload)
        response.raise_for_status()
        return response.content

    def get_metrics(self) -> List[Dict[str, Any]]:
        response = httpx.get(f"{self.base_url}/api/metrics")
        response.raise_for_status()
        return response.json()

    def get_logs(self, lines: int = 100) -> str:
        response = httpx.get(f"{self.base_url}/api/metrics/logs?lines={lines}")
        response.raise_for_status()
        return response.json().get("logs", "")

    def clear_metrics(self) -> None:
        response = httpx.post(f"{self.base_url}/api/metrics/clear")
        response.raise_for_status()


client = DeadlockAPIClient(API_URL)


def load_css() -> None:
    # Attempt to load custom theme.css first
    css_path = Path(__file__).resolve().parent / "assets" / "theme.css"
    if css_path.exists():
        with css_path.open("r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        # Fallback to style.css if theme.css is not found
        fallback_path = Path(__file__).resolve().parent / "style.css"
        if fallback_path.exists():
            with fallback_path.open("r", encoding="utf-8") as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def render_custom_table(df: pd.DataFrame) -> None:
    """Renders a pandas DataFrame as a beautiful custom HTML table with dark theme & zebra rows."""
    if df.empty:
        st.info("No data entries to display.")
        return
    # Convert df to HTML table
    html_table = df.to_html(classes="custom-table", index=False)
    st.markdown(f'<div class="custom-table-container">{html_table}</div>', unsafe_allow_html=True)


def main() -> None:
    load_css()

    # Retrieve latest state
    try:
        state = client.get_state()
    except Exception as e:
        st.error(f"Cannot connect to the backend API at {API_URL}. Is the FastAPI server running?")
        st.info("Run `python -m uvicorn src.presentation.api.main:app --reload` to start the backend API.")
        st.stop()

    processes = state["processes"]
    resources = state["resources"]
    allocations = state["allocations"]
    requests = state["requests"]
    deadlock = state["deadlock"]
    timeline = state["timeline"]

    # Calculate waiting and running process statistics
    running_count = sum(1 for p in processes if p["state"] == "Running")
    waiting_count = sum(1 for p in processes if p["state"] in {"Waiting", "Blocked"})

    # Sidebar settings
    with st.sidebar:
        # Branded Logo Section
        st.markdown(
            """
            <div class="sidebar-brand-container">
                <div class="sidebar-logo">Ω</div>
                <div class="sidebar-brand-name">DeadlockAI Enterprise</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.subheader("Controls & Customization")
        
        # Optional Light Mode Toggle
        light_mode = st.toggle("Light Mode Toggle", value=False, key="theme_toggle")
        if light_mode:
            st.markdown(
                """
                <style>
                :root {
                    --bg-main: #F8FAFC;
                    --bg-sidebar: #F1F5F9;
                    --bg-card: #FFFFFF;
                    --bg-card-hover: #F8FAFC;
                    --border-color: #E2E8F0;
                    --border-hover: #CBD5E1;
                    --text-primary: #0F172A;
                    --text-secondary: #334155;
                    --text-muted: #64748B;
                    --glass-bg: rgba(255, 255, 255, 0.75);
                    --glass-border: rgba(226, 232, 240, 0.8);
                    --shadow-glow: 0 0 20px 2px rgba(37, 99, 235, 0.04);
                }
                .stApp, [data-testid="stAppViewContainer"], [data-testid="stSidebar"], [data-testid="stHeader"] {
                    background-color: var(--bg-main) !important;
                    color: var(--text-primary) !important;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )

        if st.button("Reset Entire System", type="secondary", use_container_width=True):
            try:
                client.reset()
                st.success("System state reset completed.")
                st.rerun()
            except Exception as e:
                st.error(str(e))

        st.markdown("---")
        st.subheader("Simulation Safety Status")
        
        # Multi-state Status Banner mapping
        if deadlock["is_deadlocked"]:
            status_class = "state-deadlock"
            status_label = "DEADLOCK DETECTED"
            status_desc = f"Deadlock cycle identified containing nodes: {', '.join(deadlock['cycle'])}"
        elif waiting_count > 0:
            status_class = "state-unsafe"
            status_label = "UNSAFE STATE"
            status_desc = f"Warning: {waiting_count} processes currently blocked or waiting for resources."
        else:
            status_class = "state-safe"
            status_label = "SAFE STATE"
            status_desc = "Optimal condition. All active processes running successfully."

        st.markdown(
            f"""
            <div class="status-badge {status_class}">
                <div class="status-header-container">
                    <span class="status-indicator-dot"></span>
                    <span class="status-title-text">{status_label}</span>
                </div>
                <p class="status-desc">{status_desc}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Branded Header & Sticky Navigation
    st.markdown(
        """
        <div class="sticky-nav" style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; padding-bottom: 12px;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 1.6rem;">🛡️</span>
                <h1 style="margin: 0; font-size: 1.5rem; font-weight: 800; letter-spacing: -0.03em;">DeadlockAI Enterprise <span style="font-size: 0.75rem; font-weight: 600; padding: 3px 8px; border-radius: 12px; background: rgba(37, 99, 235, 0.12); border: 1px solid rgba(37, 99, 235, 0.3); color: var(--primary); margin-left: 6px; vertical-align: middle;">v1.1.0</span></h1>
            </div>
            <div style="font-size: 0.825rem; color: var(--text-muted); font-weight: 500;">
                Enterprise Security & Resource Allocation Lab
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Glassmorphic responsive cards layout with SVGs and trend indicators
    icon_process = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="8" rx="2" ry="2"></rect><rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect><line x1="6" y1="8" x2="6.01" y2="8"></line><line x1="6" y1="18" x2="6.01" y2="18"></line></svg>'
    icon_resource = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>'
    icon_allocation = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>'
    icon_waiting = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>'

    st.markdown(
        f"""
        <div class="stat-container">
            <div class="stat-card primary-border">
                <div class="stat-header">
                    <span class="stat-title">Total Processes</span>
                    <span class="stat-icon">{icon_process}</span>
                </div>
                <div class="stat-body">
                    <span class="stat-value">{len(processes)}</span>
                    <span class="stat-trend up">{running_count} Running</span>
                </div>
            </div>
            <div class="stat-card secondary-border">
                <div class="stat-header">
                    <span class="stat-title">Total Resources</span>
                    <span class="stat-icon">{icon_resource}</span>
                </div>
                <div class="stat-body">
                    <span class="stat-value">{len(resources)}</span>
                    <span class="stat-trend neutral">Active</span>
                </div>
            </div>
            <div class="stat-card success-border">
                <div class="stat-header">
                    <span class="stat-title">Active Allocations</span>
                    <span class="stat-icon">{icon_allocation}</span>
                </div>
                <div class="stat-body">
                    <span class="stat-value">{len(allocations)}</span>
                    <span class="stat-trend up">Assigned</span>
                </div>
            </div>
            <div class="stat-card {'danger-border' if waiting_count > 0 else 'warning-border'}">
                <div class="stat-header">
                    <span class="stat-title">Waiting Processes</span>
                    <span class="stat-icon">{icon_waiting}</span>
                </div>
                <div class="stat-body">
                    <span class="stat-value">{waiting_count}</span>
                    <span class="stat-trend {'up' if waiting_count > 0 else 'neutral'}">
                        { 'Warning' if waiting_count > 0 else 'Ideal' }
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Main Workspace Tabs with Vercel styling
    tabs = st.tabs([
        "Dashboard & Graph",
        "Processes",
        "Resources",
        "Banker's Safety Model",
        "AI Cognitive Diagnosis",
        "Monitoring & Performance",
    ])

    # Helper function to render RAG graph
    def draw_rag_graph(
        processes: List[Dict],
        resources: List[Dict],
        allocations: List[Dict],
        requests: List[Dict],
        cycle: List[str],
        zoom: float = 1.0
    ) -> BytesIO:
        g = nx.DiGraph()
        for p in processes:
            g.add_node(p["pid"], kind="process")
        for r in resources:
            g.add_node(r["rid"], kind="resource")

        for a in allocations:
            g.add_edge(a["resource"], a["process"], edge_type="allocation")
        for r_edge in requests:
            g.add_edge(r_edge["process"], r_edge["resource"], edge_type="request")

        fig, ax = plt.subplots(figsize=(10, 6))
        try:
            pos = nx.spring_layout(g, seed=42)

            proc_nodes = [n for n, attr in g.nodes(data=True) if attr.get("kind") == "process"]
            res_nodes = [n for n, attr in g.nodes(data=True) if attr.get("kind") == "resource"]

            # Redesigned Node Colors: Process -> #2563EB, Resource -> #7C3AED
            nx.draw_networkx_nodes(
                g,
                pos,
                nodelist=proc_nodes,
                node_color="#2563EB",
                node_size=int(1100 * zoom),
                ax=ax,
            )
            nx.draw_networkx_nodes(
                g,
                pos,
                nodelist=res_nodes,
                node_color="#7C3AED",
                node_size=int(1100 * zoom),
                ax=ax,
            )

            # Highlight cycle edges in red (#EF4444)
            cycle_edges = set()
            if cycle and len(cycle) >= 2:
                for i in range(len(cycle) - 1):
                    cycle_edges.add((cycle[i], cycle[i + 1]))

            normal_edges = [e for e in g.edges if e not in cycle_edges]

            # Soft gray border color for standard edges
            nx.draw_networkx_edges(
                g,
                pos,
                edgelist=normal_edges,
                edge_color="#475569",
                arrows=True,
                arrowstyle='-|>',
                arrowsize=14,
                width=1.8,
                ax=ax,
                connectionstyle="arc3,rad=0.15"  # Curved edges to prevent overlap
            )
            if cycle_edges:
                nx.draw_networkx_edges(
                    g,
                    pos,
                    edgelist=list(cycle_edges),
                    edge_color="#EF4444",
                    arrows=True,
                    arrowstyle='-|>',
                    arrowsize=18,
                    width=2.8,
                    ax=ax,
                    connectionstyle="arc3,rad=0.15"
                )

            nx.draw_networkx_labels(
                g,
                pos,
                font_color="#F8FAFC",
                font_size=int(9 * zoom),
                font_weight="bold",
                ax=ax,
            )

            ax.axis("off")
            fig.patch.set_facecolor("none")
            ax.set_facecolor("none")

            buffer = BytesIO()
            fig.tight_layout()
            fig.savefig(buffer, format="png", dpi=150, facecolor=fig.get_facecolor(), edgecolor="none")
            buffer.seek(0)
            return buffer
        finally:
            plt.close(fig)

    with tabs[0]:
        col1, col2 = st.columns([3, 2])
        with col1:
            st.subheader("Resource Allocation Graph (RAG)")
            
            # Sub-header controls for graph scaling
            g_col1, g_col2 = st.columns([1, 1])
            with g_col1:
                zoom_val = st.slider("Graph Node & Text Zoom", min_value=0.5, max_value=2.0, value=1.0, step=0.1)
            
            if processes or resources:
                img = draw_rag_graph(
                    processes,
                    resources,
                    allocations,
                    requests,
                    deadlock["cycle"],
                    zoom=zoom_val
                )
                st.image(img, use_container_width=True)
            else:
                st.info("RAG is currently empty. Add processes and resources to visualize relationships.")

        with col2:
            st.subheader("Interactive Edge Routing")
            if processes and resources:
                edge_type = st.radio("Edge Action Type", ["Allocate (Resource -> Process)", "Request (Process -> Resource)", "Release (Resource -> Process)"])

                if edge_type == "Allocate (Resource -> Process)":
                    a_rid = st.selectbox("Select Resource", [r["rid"] for r in resources], key="alloc_rid")
                    a_pid = st.selectbox("Select Target Process", [p["pid"] for p in processes], key="alloc_pid")
                    if st.button("Allocate Edge", type="primary"):
                        try:
                            client.allocate(a_rid, a_pid)
                            st.success(f"Allocated {a_rid} to {a_pid}")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))

                elif edge_type == "Request (Process -> Resource)":
                    r_pid = st.selectbox("Select Requesting Process", [p["pid"] for p in processes], key="req_pid")
                    r_rid = st.selectbox("Select Requested Resource", [r["rid"] for r in resources], key="req_rid")
                    if st.button("Request Edge", type="primary"):
                        try:
                            client.request(r_pid, r_rid)
                            st.warning(f"Request edge added: {r_pid} -> {r_rid}")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))

                elif edge_type == "Release (Resource -> Process)":
                    rel_rid = st.selectbox("Select Resource", [r["rid"] for r in resources], key="rel_rid")
                    rel_pid = st.selectbox("Select Allocated Process", [p["pid"] for p in processes], key="rel_pid")
                    if st.button("Release Edge", type="primary"):
                        try:
                            client.release(rel_rid, rel_pid)
                            st.success(f"Released {rel_rid} from {rel_pid}")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
            else:
                st.info("Setup processes and resources first to routing edges.")

        # HTML Legend Panel
        st.markdown(
            """
            <div class="graph-card">
                <div class="graph-header">
                    <span style="font-weight: 700; font-size: 0.9rem; color: var(--text-primary);">RAG Graph Visualization Legend</span>
                </div>
                <div class="graph-legend">
                    <div class="legend-item">
                        <span class="legend-color process"></span>
                        <span>Processes (Blue)</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-color resource"></span>
                        <span>Resources (Purple)</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-color allocation" style="background-color: #475569;"></span>
                        <span>Allocation Direction (Resource ➔ Process)</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-color request" style="background-color: #475569;"></span>
                        <span>Request Direction (Process ➔ Resource)</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-color deadlock-edge"></span>
                        <span>Highlighted Deadlock Cycle (Red)</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.subheader("Timeline Events")
        if timeline:
            render_custom_table(pd.DataFrame(timeline))
        else:
            st.info("No timeline events captured yet.")

    with tabs[1]:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("Add Process")
            p_id = st.text_input("Process ID", value="P4", key="add_proc_id")
            p_state = st.selectbox("State", ["Running", "Waiting", "Blocked", "Terminated"], index=1)
            if st.button("Create Process", type="primary"):
                try:
                    client.create_process(p_id.strip(), p_state)
                    st.success(f"Process {p_id} created successfully.")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

        with col2:
            st.subheader("Process Control Panel")
            if processes:
                selected_p = st.selectbox("Select Target Process", [p["pid"] for p in processes], key="ctrl_pid")
                p_action = st.radio("Action", ["Modify State", "Delete Process"])

                if p_action == "Modify State":
                    new_p_state = st.selectbox("New State", ["Running", "Waiting", "Blocked", "Terminated"])
                    if st.button("Update Process State"):
                        try:
                            client.update_process_state(selected_p, new_p_state)
                            st.success(f"Process {selected_p} state modified to {new_p_state}")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
                else:
                    if st.button("Delete Process"):
                        try:
                            client.delete_process(selected_p)
                            st.success(f"Deleted process {selected_p}")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))

        st.subheader("Active Processes Registry")
        if processes:
            render_custom_table(pd.DataFrame(processes))
        else:
            st.info("No active processes.")

    with tabs[2]:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("Add Resource")
            r_id = st.text_input("Resource ID", value="R4", key="add_res_id")
            r_inst = st.number_input("Total Instances", min_value=1, step=1, value=1)
            if st.button("Create Resource", type="primary"):
                try:
                    client.create_resource(r_id.strip(), int(r_inst))
                    st.success(f"Resource {r_id} created successfully.")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

        with col2:
            st.subheader("Resource Control Panel")
            if resources:
                selected_r = st.selectbox("Select Target Resource", [r["rid"] for r in resources], key="ctrl_rid")
                r_action = st.radio("Action", ["Modify Instance Limit", "Release One Instance", "Delete Resource"])

                if r_action == "Modify Instance Limit":
                    new_r_inst = st.number_input("Modify Total Instances", min_value=1, step=1, value=1)
                    if st.button("Apply Limits"):
                        try:
                            client.update_resource_instances(selected_r, int(new_r_inst))
                            st.success(f"Resource {selected_r} total instances set to {new_r_inst}")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
                elif r_action == "Release One Instance":
                    if st.button("Release One Instance"):
                        try:
                            client.release_one_instance(selected_r)
                            st.success(f"Released one instance of resource {selected_r}")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
                else:
                    if st.button("Delete Resource"):
                        try:
                            client.delete_resource(selected_r)
                            st.success(f"Deleted resource {selected_r}")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))

        st.subheader("Active Resources Registry")
        if resources:
            render_custom_table(pd.DataFrame(resources))
        else:
            st.info("No active resources.")

    with tabs[3]:
        st.subheader("Banker's Safety Algorithm Simulator")
        st.caption("Interactive safe sequence solver and need matrix trace.")

        banker_proc_default = "P1,P2,P3"
        banker_alloc_default = "1,0,1\n0,1,0\n1,0,0"
        banker_max_default = "2,1,1\n1,2,1\n2,1,1"
        banker_avail_default = "1,1,1"

        b_col1, b_col2 = st.columns([1, 1])
        with b_col1:
            b_names = st.text_input("Process Identifiers (comma-separated)", value=banker_proc_default)
            b_alloc = st.text_area("Allocation Matrix (comma-separated rows)", value=banker_alloc_default, height=120)
        with b_col2:
            b_max = st.text_area("Maximum Demand Matrix (comma-separated rows)", value=banker_max_default, height=120)
            b_avail = st.text_input("Available Vector (comma-separated)", value=banker_avail_default)

        if st.button("Run Banker's Safety Verification", type="primary"):
            try:
                names = [x.strip() for x in b_names.split(",") if x.strip()]
                alloc = [[int(val.strip()) for val in r.split(",")] for r in b_alloc.splitlines() if r.strip()]
                maximum = [[int(val.strip()) for val in r.split(",")] for r in b_max.splitlines() if r.strip()]
                avail = [int(val.strip()) for val in b_avail.split(",") if val.strip()]

                res = client.evaluate_bankers(alloc, maximum, avail, names)

                # Store result in session state for AI explainer usage
                st.session_state.banker_summary = res["explanation"]

                st.markdown("### Evaluation Output")
                badge_class = "state-safe" if res["safe"] else "state-unsafe"
                badge_label = "SAFE" if res["safe"] else "UNSAFE"
                
                st.markdown(
                    f"""
                    <div class="status-badge {badge_class}" style="margin-bottom: 20px;">
                        <div class="status-header-container">
                            <span class="status-indicator-dot"></span>
                            <span class="status-title-text">Banker's: {badge_label}</span>
                        </div>
                        <p class="status-desc">{res['explanation']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if res["safe_sequence"]:
                    st.info(f"🟢 Safe sequence found: {' ➔ '.join(res['safe_sequence'])}")

                col_n, col_w = st.columns(2)
                with col_n:
                    st.subheader("Need Matrix (Maximum - Allocation)")
                    need_df = pd.DataFrame(res["need_matrix"], index=names).reset_index().rename(columns={"index": "Process ID"})
                    render_custom_table(need_df)
                with col_w:
                    st.subheader("Available Vectors Trace")
                    render_custom_table(pd.DataFrame(res["work_trace"]))

            except Exception as e:
                st.error(f"Computation failure: {e}")

    with tabs[4]:
        st.subheader("Structured AI Deadlock Analysis")
        st.caption("Detailed resolution recommendations generated by Gemini API.")

        banker_summary = st.session_state.get("banker_summary", "No Banker run trace executed yet.")
        st.text_area("Banker's Algorithm Summary to pass to Gemini", value=banker_summary, disabled=True, height=70)

        if st.button("Generate Diagnostic Report", type="primary"):
            with st.spinner("Invoking Gemini cognitive analysis..."):
                try:
                    ai_res = client.explain_deadlock(
                        cycle=deadlock["cycle"],
                        processes=deadlock["processes"],
                        resources=deadlock["resources"],
                        banker_summary=banker_summary,
                    )
                    st.session_state.ai_explanation = ai_res
                    st.success("AI Explanation generated and cached.")
                except Exception as e:
                    st.error(f"Cognitive AI error: {e}")

        ai_exp = st.session_state.get("ai_explanation")
        if ai_exp:
            st.markdown(f"### 🔍 Diagnosis: Why It Occurred")
            st.markdown(ai_exp["why_occurred"])

            c_col1, c_col2 = st.columns(2)
            with c_col1:
                st.markdown("### 🏷️ Coffman Conditions Satisfied")
                for cond in ai_exp["coffman_conditions"]:
                    st.markdown(f"- {cond}")
            with c_col2:
                st.markdown("### ⚠️ Key Blockers & Processes")
                st.markdown(f"**Blocked Processes**: {', '.join(ai_exp['processes_involved']) or 'None'}")
                st.markdown(f"**Blocking Resources**: {', '.join(ai_exp['resources_blocking']) or 'None'}")

            r_col1, r_col2 = st.columns(2)
            with r_col1:
                st.markdown("### 🔧 Immediate Remedies (Resolution)")
                for val in ai_exp["resolution_strategies"]:
                    st.markdown(f"- {val}")
            with r_col2:
                st.markdown("### 🛡️ Long-term Mitigation (Prevention)")
                for val in ai_exp["prevention_techniques"]:
                    st.markdown(f"- {val}")

            st.markdown("### 📈 Banker's Safety Recommendation")
            st.info(ai_exp["banker_recommendation"])

            st.markdown("---")
            st.subheader("Export Enterprise Report")
            payload = {
                "processes": processes,
                "resources": resources,
                "allocations": allocations,
                "deadlock_cycle": deadlock["cycle"],
                "ai_explanation": ai_exp,
            }

            try:
                report_bytes = client.download_report(payload)
                st.download_button(
                    label="📥 Download Enterprise PDF Report",
                    data=report_bytes,
                    file_name="deadlockai_enterprise_report.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"Failed to load PDF report generator: {e}")
        else:
            st.info("Trigger 'Generate Diagnostic Report' to display Gemini AI insights.")

    with tabs[5]:
        st.subheader("Application Metrics & Performance Monitor")

        try:
            metrics_list = client.get_metrics()
        except Exception as e:
            st.error(f"Cannot retrieve metrics: {e}")
            metrics_list = []

        if metrics_list:
            metrics_df = pd.DataFrame(metrics_list)

            # Plot interactive latency graphs using Plotly
            latency_df = metrics_df[metrics_df["metric_type"] == "performance"]
            if not latency_df.empty:
                st.subheader("API Latency (milliseconds)")
                # Parse timing
                latency_df["timestamp"] = pd.to_datetime(latency_df["timestamp"])
                latency_df = latency_df.sort_values("timestamp")
                
                # Interactive Plotly area chart
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=latency_df["timestamp"],
                    y=latency_df["value"],
                    mode='lines',
                    fill='tozeroy',
                    name='Latency (ms)',
                    line=dict(color='#2563EB', width=2.5),
                    fillcolor='rgba(37, 99, 235, 0.15)',
                    hovertemplate='<b>Time</b>: %{x}<br><b>Latency</b>: %{y:.2f} ms<extra></extra>'
                ))
                
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=0, r=0, t=10, b=0),
                    height=240,
                    xaxis=dict(
                        showgrid=True,
                        gridcolor="#334155",
                        zeroline=False,
                    ),
                    yaxis=dict(
                        showgrid=True,
                        gridcolor="#334155",
                        zeroline=False,
                    ),
                    hovermode="x unified"
                )
                st.plotly_chart(fig, use_container_width=True)

            # Token metrics
            token_df = metrics_df[metrics_df["metric_type"] == "token_count"]
            if not token_df.empty:
                st.subheader("Gemini Cognitive Token Consumption")
                render_custom_table(token_df[["timestamp", "name", "value"]])

            # Error metrics
            error_df = metrics_df[metrics_df["metric_type"] == "error"]
            if not error_df.empty:
                st.subheader("Tracked Application Errors")
                st.error(f"Captured {len(error_df)} backend errors in metrics store.")
                render_custom_table(error_df)

            if st.button("Reset Metrics database"):
                try:
                    client.clear_metrics()
                    st.success("Cleared metrics database.")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
        else:
            st.info("No performance metrics logged yet. Make API calls to populate monitoring data.")

        st.subheader("Live System Logs")
        try:
            logs_text = client.get_logs(lines=100)
            st.code(logs_text, language="log")
        except Exception as e:
            st.error(f"Cannot read log tails: {e}")


if __name__ == "__main__":
    main()
