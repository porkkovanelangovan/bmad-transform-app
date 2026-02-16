"""
Connectors — REST API clients for Jira Cloud and ServiceNow.
Each connector reads credentials from environment variables and fails gracefully.
"""

import base64
import logging
import os
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Configuration helpers
# ──────────────────────────────────────────────

def is_jira_configured() -> bool:
    return bool(
        os.getenv("JIRA_BASE_URL")
        and os.getenv("JIRA_EMAIL")
        and os.getenv("JIRA_API_TOKEN")
    )


def is_servicenow_configured() -> bool:
    return bool(
        os.getenv("SERVICENOW_INSTANCE")
        and os.getenv("SERVICENOW_USERNAME")
        and os.getenv("SERVICENOW_PASSWORD")
    )


# ──────────────────────────────────────────────
# Jira Cloud Connector
# ──────────────────────────────────────────────

async def fetch_jira_workflows(project_key: str | None = None) -> dict:
    """
    Fetch workflow data from Jira Cloud.
    Extracts process steps from workflow statuses and computes cycle time estimates.
    Returns {source, steps, project_summary}.
    """
    base_url = os.getenv("JIRA_BASE_URL", "").rstrip("/")
    email = os.getenv("JIRA_EMAIL", "")
    token = os.getenv("JIRA_API_TOKEN", "")

    if not base_url or not email or not token:
        return {"error": "Jira not configured. Set JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN."}

    cred = base64.b64encode(f"{email}:{token}".encode()).decode()
    headers = {
        "Authorization": f"Basic {cred}",
        "Accept": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # 1. Get projects
            if not project_key:
                resp = await client.get(
                    f"{base_url}/rest/api/3/project",
                    headers=headers,
                )
                resp.raise_for_status()
                projects = resp.json()
                if not projects:
                    return {"error": "No Jira projects found"}
                project_key = projects[0]["key"]

            # 2. Search recent issues for cycle time data
            jql = f"project={project_key} ORDER BY created DESC"
            resp = await client.get(
                f"{base_url}/rest/api/3/search",
                params={
                    "jql": jql,
                    "maxResults": 50,
                    "fields": "status,created,resolutiondate,summary,issuetype",
                },
                headers=headers,
            )
            resp.raise_for_status()
            search_data = resp.json()
            issues = search_data.get("issues", [])

            # 3. Get workflow statuses
            resp = await client.get(
                f"{base_url}/rest/api/3/project/{project_key}/statuses",
                headers=headers,
            )
            resp.raise_for_status()
            status_data = resp.json()

            # Extract unique statuses from the first issue type's workflow
            statuses = []
            seen_names = set()
            for issue_type_statuses in status_data:
                for status in issue_type_statuses.get("statuses", []):
                    name = status.get("name", "")
                    if name and name not in seen_names:
                        seen_names.add(name)
                        statuses.append({
                            "name": name,
                            "category": status.get("statusCategory", {}).get("key", ""),
                            "category_name": status.get("statusCategory", {}).get("name", ""),
                        })

            # Map statuses to steps
            CATEGORY_MAP = {
                "new": "trigger",
                "undefined": "process",
                "indeterminate": "process",
                "done": "delivery",
            }

            steps = []
            for i, status in enumerate(statuses, 1):
                step_type = CATEGORY_MAP.get(status["category"], "process")
                steps.append({
                    "step_order": i,
                    "step_name": status["name"],
                    "description": f"Jira workflow status ({status['category_name']})",
                    "step_type": step_type,
                    "process_time_hours": 0,
                    "wait_time_hours": 0,
                    "resources": "",
                    "is_bottleneck": False,
                    "notes": f"Jira status category: {status['category_name']}",
                })

            # Compute average cycle time from resolved issues
            cycle_times = []
            for issue in issues:
                fields = issue.get("fields", {})
                created = fields.get("created")
                resolved = fields.get("resolutiondate")
                if created and resolved:
                    try:
                        created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                        resolved_dt = datetime.fromisoformat(resolved.replace("Z", "+00:00"))
                        hours = (resolved_dt - created_dt).total_seconds() / 3600
                        if hours > 0:
                            cycle_times.append(hours)
                    except (ValueError, TypeError):
                        pass

            avg_cycle_hours = sum(cycle_times) / len(cycle_times) if cycle_times else 0

            # Distribute cycle time across process steps
            process_steps = [s for s in steps if s["step_type"] == "process"]
            if process_steps and avg_cycle_hours > 0:
                per_step = avg_cycle_hours / len(process_steps)
                for step in process_steps:
                    step["process_time_hours"] = round(per_step * 0.4, 1)
                    step["wait_time_hours"] = round(per_step * 0.6, 1)

            return {
                "source": "jira",
                "steps": steps,
                "project_summary": {
                    "project_key": project_key,
                    "total_issues_sampled": len(issues),
                    "resolved_issues": len(cycle_times),
                    "avg_cycle_time_hours": round(avg_cycle_hours, 1),
                    "workflow_statuses": len(statuses),
                },
            }

    except httpx.HTTPStatusError as e:
        logger.error("Jira API error: %s %s", e.response.status_code, e.response.text[:200])
        return {"error": f"Jira API error: HTTP {e.response.status_code}"}
    except Exception as e:
        logger.error("Jira connector error: %s", e)
        return {"error": f"Jira connector error: {e}"}


# ──────────────────────────────────────────────
# ServiceNow Connector
# ──────────────────────────────────────────────

async def fetch_servicenow_workflows(table: str = "incident") -> dict:
    """
    Fetch workflow/lifecycle data from ServiceNow.
    Extracts process steps from lifecycle states and computes time-in-state metrics.
    Returns {source, steps, table_summary}.
    """
    instance = os.getenv("SERVICENOW_INSTANCE", "")
    username = os.getenv("SERVICENOW_USERNAME", "")
    password = os.getenv("SERVICENOW_PASSWORD", "")

    if not instance or not username or not password:
        return {"error": "ServiceNow not configured. Set SERVICENOW_INSTANCE, SERVICENOW_USERNAME, SERVICENOW_PASSWORD."}

    base_url = f"https://{instance}.service-now.com"
    auth = (username, password)

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # 1. Get state choices for the table
            resp = await client.get(
                f"{base_url}/api/now/table/sys_choice",
                params={
                    "sysparm_query": f"name={table}^element=state",
                    "sysparm_fields": "value,label",
                    "sysparm_limit": 20,
                },
                auth=auth,
                headers={"Accept": "application/json"},
            )
            resp.raise_for_status()
            choices_data = resp.json()
            state_choices = choices_data.get("result", [])

            # 2. Get recent records for time-in-state data
            resp = await client.get(
                f"{base_url}/api/now/table/{table}",
                params={
                    "sysparm_limit": 50,
                    "sysparm_fields": "state,sys_created_on,sys_updated_on,resolved_at,closed_at,short_description",
                    "sysparm_query": "ORDERBYDESCsys_created_on",
                },
                auth=auth,
                headers={"Accept": "application/json"},
            )
            resp.raise_for_status()
            records_data = resp.json()
            records = records_data.get("result", [])

            # Map state values to step types
            # Common ServiceNow incident states: 1=New, 2=In Progress, 3=On Hold, 6=Resolved, 7=Closed
            STATE_TYPE_MAP = {
                "1": "trigger",       # New
                "2": "process",       # In Progress / Active
                "3": "decision",      # On Hold
                "4": "process",       # Awaiting
                "5": "process",       # Awaiting
                "6": "delivery",      # Resolved
                "7": "delivery",      # Closed
                "8": "delivery",      # Cancelled
            }
            # Fallback label-based mapping
            LABEL_TYPE_MAP = {
                "new": "trigger",
                "open": "trigger",
                "in progress": "process",
                "active": "process",
                "pending": "decision",
                "on hold": "decision",
                "awaiting": "decision",
                "resolved": "delivery",
                "closed": "delivery",
                "cancelled": "delivery",
                "complete": "delivery",
            }

            # Build steps from state choices
            steps = []
            for i, choice in enumerate(state_choices, 1):
                label = choice.get("label", f"State {choice.get('value', i)}")
                value = choice.get("value", "")

                step_type = STATE_TYPE_MAP.get(value)
                if not step_type:
                    label_lower = label.lower()
                    for key, stype in LABEL_TYPE_MAP.items():
                        if key in label_lower:
                            step_type = stype
                            break
                    else:
                        step_type = "process"

                steps.append({
                    "step_order": i,
                    "step_name": label,
                    "description": f"ServiceNow {table} state (value={value})",
                    "step_type": step_type,
                    "process_time_hours": 0,
                    "wait_time_hours": 0,
                    "resources": "",
                    "is_bottleneck": False,
                    "notes": f"ServiceNow table: {table}, state value: {value}",
                })

            # Compute lifecycle metrics from records
            cycle_times = []
            for record in records:
                created = record.get("sys_created_on", "")
                resolved = record.get("resolved_at", "") or record.get("closed_at", "")
                if created and resolved:
                    try:
                        created_dt = datetime.fromisoformat(created)
                        resolved_dt = datetime.fromisoformat(resolved)
                        hours = (resolved_dt - created_dt).total_seconds() / 3600
                        if hours > 0:
                            cycle_times.append(hours)
                    except (ValueError, TypeError):
                        pass

            avg_cycle_hours = sum(cycle_times) / len(cycle_times) if cycle_times else 0

            # Distribute cycle time across process steps
            process_steps = [s for s in steps if s["step_type"] == "process"]
            if process_steps and avg_cycle_hours > 0:
                per_step = avg_cycle_hours / len(process_steps)
                for step in process_steps:
                    step["process_time_hours"] = round(per_step * 0.3, 1)
                    step["wait_time_hours"] = round(per_step * 0.7, 1)

            # If no state choices found, provide default incident lifecycle
            if not steps:
                steps = [
                    {"step_order": 1, "step_name": "New", "description": "Incident created", "step_type": "trigger", "process_time_hours": 0, "wait_time_hours": 0, "resources": "", "is_bottleneck": False, "notes": f"Default {table} lifecycle"},
                    {"step_order": 2, "step_name": "In Progress", "description": "Being worked on", "step_type": "process", "process_time_hours": 0, "wait_time_hours": 0, "resources": "", "is_bottleneck": False, "notes": f"Default {table} lifecycle"},
                    {"step_order": 3, "step_name": "On Hold", "description": "Awaiting input", "step_type": "decision", "process_time_hours": 0, "wait_time_hours": 0, "resources": "", "is_bottleneck": False, "notes": f"Default {table} lifecycle"},
                    {"step_order": 4, "step_name": "Resolved", "description": "Issue resolved", "step_type": "delivery", "process_time_hours": 0, "wait_time_hours": 0, "resources": "", "is_bottleneck": False, "notes": f"Default {table} lifecycle"},
                    {"step_order": 5, "step_name": "Closed", "description": "Ticket closed", "step_type": "delivery", "process_time_hours": 0, "wait_time_hours": 0, "resources": "", "is_bottleneck": False, "notes": f"Default {table} lifecycle"},
                ]

            return {
                "source": "servicenow",
                "steps": steps,
                "table_summary": {
                    "table": table,
                    "total_records_sampled": len(records),
                    "resolved_records": len(cycle_times),
                    "avg_cycle_time_hours": round(avg_cycle_hours, 1),
                    "lifecycle_states": len(steps),
                },
            }

    except httpx.HTTPStatusError as e:
        logger.error("ServiceNow API error: %s %s", e.response.status_code, e.response.text[:200])
        return {"error": f"ServiceNow API error: HTTP {e.response.status_code}"}
    except Exception as e:
        logger.error("ServiceNow connector error: %s", e)
        return {"error": f"ServiceNow connector error: {e}"}
