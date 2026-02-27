"""
AI Research Module — OpenAI GPT integration for value stream synthesis.
Gracefully degrades if openai package or API key is not available.
"""

import json
import os


def is_openai_available() -> bool:
    """Check if openai package is installed AND OPENAI_API_KEY env var is set."""
    if not os.getenv("OPENAI_API_KEY"):
        return False
    try:
        import openai  # noqa: F401
        return True
    except ImportError:
        return False


def extract_list(result, key=None):
    """Extract a list from an OpenAI JSON result (handles wrapped or unwrapped)."""
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        if key and key in result:
            v = result[key]
            return v if isinstance(v, list) else []
        for v in result.values():
            if isinstance(v, list):
                return v
    return []


async def call_openai_json(prompt: str, system: str = "You are an expert business transformation consultant. Return valid JSON only."):
    """Generic helper to call OpenAI and parse JSON response."""
    if not is_openai_available():
        return None
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI()
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=4000,
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("call_openai_json failed: %s", e)
        return None


async def research_value_stream(
    segment_name: str,
    industry: str,
    org_name: str,
    org_context: dict,
    competitor_data: dict,
    sources_context: list[dict],
    rag_context: str = "",
) -> dict | None:
    """Use OpenAI GPT to synthesize gathered source data into a comprehensive value stream.

    Returns {steps, overall_metrics, competitor_benchmarks} or None on failure.
    """
    if not is_openai_available():
        return None

    try:
        from openai import AsyncOpenAI

        system_prompt = (
            "You are a lean/six sigma expert specializing in value stream mapping. "
            "Given context about an organization, its industry, competitors, and gathered data sources, "
            "synthesize a comprehensive value stream map.\n\n"
            "Return a JSON object with exactly this structure:\n"
            "{\n"
            '  "steps": [\n'
            "    {\n"
            '      "step_order": 1,\n'
            '      "step_name": "Step Name",\n'
            '      "description": "What happens in this step",\n'
            '      "step_type": "trigger|process|decision|delivery",\n'
            '      "process_time_hours": 1.0,\n'
            '      "wait_time_hours": 2.0,\n'
            '      "resources": "Who/what performs this",\n'
            '      "is_bottleneck": false,\n'
            '      "notes": "Additional context"\n'
            "    }\n"
            "  ],\n"
            '  "overall_metrics": {\n'
            '    "total_lead_time_hours": 50.0,\n'
            '    "total_process_time_hours": 15.0,\n'
            '    "total_wait_time_hours": 35.0,\n'
            '    "flow_efficiency": 30.0,\n'
            '    "bottleneck_step": "Step Name",\n'
            '    "bottleneck_reason": "Why this step is the bottleneck"\n'
            "  },\n"
            '  "competitor_benchmarks": [\n'
            "    {\n"
            '      "competitor_name": "Competitor Name",\n'
            '      "total_lead_time_hours": 45.0,\n'
            '      "total_process_time_hours": 12.0,\n'
            '      "flow_efficiency": 26.7,\n'
            '      "bottleneck_step": "Step Name",\n'
            '      "key_differentiator": "What they do differently",\n'
            '      "automation_level": "high|medium|low",\n'
            '      "technology_stack": "Key technologies used",\n'
            '      "notes": "Comparative insight"\n'
            "    }\n"
            "  ]\n"
            "}\n\n"
            "Guidelines:\n"
            "- Include 6-10 steps covering the full end-to-end process\n"
            "- Use realistic time estimates based on industry data\n"
            "- Mark exactly one step as is_bottleneck: true\n"
            "- Include 2-4 competitor benchmarks with detailed operational comparisons\n"
            "- For competitor benchmarks, include specific operational differences:\n"
            "  * How their process times compare to the organization\n"
            "  * Their automation level (high/medium/low)\n"
            "  * Key technologies or approaches they use differently\n"
            "  * What makes them more or less efficient\n"
            "- Flow efficiency = (total_process_time / total_lead_time) * 100\n"
            "- Ensure all numeric values are consistent"
        )

        # Build user prompt with gathered context
        context_parts = [
            f"Organization: {org_name}",
            f"Industry: {industry}",
            f"Value Stream Segment: {segment_name}",
        ]

        if org_context:
            context_parts.append(f"Organization Context: {json.dumps(org_context, default=str)}")

        if competitor_data and competitor_data.get("competitor_names"):
            context_parts.append(
                f"Known Competitors: {', '.join(competitor_data['competitor_names'])}"
            )
            if competitor_data.get("peers"):
                peer_summaries = []
                for p in competitor_data["peers"][:3]:
                    profile = p.get("profile", {})
                    financials = p.get("financials", {})
                    summary = f"{profile.get('name', 'Unknown')}"
                    if financials.get("market_cap"):
                        summary += f" (Market Cap: ${financials['market_cap']:,.0f})"
                    if financials.get("profit_margin"):
                        summary += f" (Margin: {financials['profit_margin']:.1%})"
                    peer_summaries.append(summary)
                context_parts.append(f"Competitor Financial Data: {'; '.join(peer_summaries)}")
            # Include competitor operational data if available
            if competitor_data.get("competitor_operations"):
                for comp_ops in competitor_data["competitor_operations"][:3]:
                    context_parts.append(
                        f"Competitor Operations ({comp_ops.get('name', 'Unknown')}): "
                        f"{json.dumps(comp_ops, default=str)}"
                    )

        if sources_context:
            for src in sources_context:
                source_name = src.get("source", "unknown")
                if source_name == "industry_benchmarks" and src.get("industry_kpis"):
                    context_parts.append(
                        f"Industry Benchmarks: {json.dumps(src['industry_kpis'], default=str)}"
                    )
                elif source_name == "erp_simulation" and src.get("steps"):
                    erp_summary = [
                        f"{s['step_name']} (vol: {s['monthly_volume']}/mo, SLA: {s['sla_target_hours']}h)"
                        for s in src["steps"][:5]
                    ]
                    context_parts.append(f"ERP System Data: {'; '.join(erp_summary)}")
                elif source_name == "web_search" and src.get("references"):
                    ref_summary = [
                        f"{r['title']}: {r['key_finding']}" for r in src["references"][:3]
                    ]
                    context_parts.append(f"Industry Research: {'; '.join(ref_summary)}")
                elif source_name == "competitor_operations" and src.get("benchmarks"):
                    context_parts.append(
                        f"Competitor Operational Benchmarks: {json.dumps(src['benchmarks'], default=str)}"
                    )

        # Include RAG context from organization knowledge base
        if rag_context:
            context_parts.append(
                f"\n--- Organization Knowledge Base (Retrieved Documents) ---\n{rag_context}"
            )

        user_prompt = (
            "Based on the following context, generate a comprehensive value stream map:\n\n"
            + "\n".join(context_parts)
        )

        client = AsyncOpenAI()
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=3000,
        )

        content = response.choices[0].message.content
        result = json.loads(content)

        # Validate minimal structure
        if "steps" not in result or not result["steps"]:
            return None

        # Ensure overall_metrics exists
        if "overall_metrics" not in result:
            steps = result["steps"]
            total_pt = sum(s.get("process_time_hours", 0) for s in steps)
            total_wt = sum(s.get("wait_time_hours", 0) for s in steps)
            total_lt = total_pt + total_wt
            result["overall_metrics"] = {
                "total_lead_time_hours": round(total_lt, 1),
                "total_process_time_hours": round(total_pt, 1),
                "total_wait_time_hours": round(total_wt, 1),
                "flow_efficiency": round((total_pt / total_lt * 100) if total_lt > 0 else 0, 1),
                "bottleneck_step": next(
                    (s["step_name"] for s in steps if s.get("is_bottleneck")),
                    steps[0]["step_name"] if steps else "Unknown",
                ),
                "bottleneck_reason": "Identified by AI analysis",
            }

        if "competitor_benchmarks" not in result:
            result["competitor_benchmarks"] = []

        return result

    except Exception:
        return None


async def research_competitor_benchmarks(
    segment_name: str,
    industry: str,
    org_name: str,
    competitors: list[str],
    org_value_stream_data: dict = None,
    rag_context: str = "",
) -> dict | None:
    """Use OpenAI GPT to generate detailed competitor operational benchmarks.

    Focused on operational/process data for value stream benchmarking.
    Returns {benchmarks: [...], industry_best_practices: [...]} or None on failure.
    """
    if not is_openai_available():
        return None

    try:
        from openai import AsyncOpenAI

        system_prompt = (
            "You are an operations research expert specializing in competitive benchmarking "
            "and value stream analysis. Given an organization's value stream and competitors, "
            "generate detailed operational benchmarks for each competitor.\n\n"
            "Return a JSON object with this structure:\n"
            "{\n"
            '  "benchmarks": [\n'
            "    {\n"
            '      "competitor_name": "Competitor Name",\n'
            '      "segment_name": "Value Stream Segment",\n'
            '      "total_lead_time_hours": 45.0,\n'
            '      "total_process_time_hours": 12.0,\n'
            '      "flow_efficiency": 26.7,\n'
            '      "bottleneck_step": "Their bottleneck",\n'
            '      "automation_level": "high|medium|low",\n'
            '      "digital_maturity": "leader|advanced|developing|basic",\n'
            '      "technology_stack": "Key technologies (e.g., RPA, AI/ML, cloud-native)",\n'
            '      "key_differentiator": "What they do differently or better",\n'
            '      "process_innovations": ["Innovation 1", "Innovation 2"],\n'
            '      "estimated_cost_per_transaction": 15.50,\n'
            '      "customer_satisfaction_score": 4.2,\n'
            '      "notes": "Detailed comparative insight"\n'
            "    }\n"
            "  ],\n"
            '  "industry_best_practices": [\n'
            "    {\n"
            '      "practice": "Best practice name",\n'
            '      "description": "What it involves",\n'
            '      "adoption_rate": "65% of top performers",\n'
            '      "impact": "20-30% reduction in lead time",\n'
            '      "applicable_steps": ["Step 1", "Step 2"]\n'
            "    }\n"
            "  ]\n"
            "}\n\n"
            "Guidelines:\n"
            "- Generate benchmarks for each known competitor\n"
            "- Use realistic, industry-appropriate metrics\n"
            "- Include specific technology and automation differences\n"
            "- Identify 3-5 industry best practices for this value stream\n"
            "- Base estimates on publicly available information about these companies\n"
            "- Be specific about what makes each competitor more or less efficient"
        )

        context_parts = [
            f"Organization: {org_name}",
            f"Industry: {industry}",
            f"Value Stream Segment: {segment_name}",
            f"Competitors to Benchmark: {', '.join(competitors) if competitors else 'Identify top competitors'}",
        ]

        if org_value_stream_data:
            metrics = org_value_stream_data.get("metrics", {})
            if metrics:
                context_parts.append(
                    f"Organization's Current Metrics: Lead Time={metrics.get('total_lead_time_hours', 'N/A')}h, "
                    f"Process Time={metrics.get('total_process_time_hours', 'N/A')}h, "
                    f"Flow Efficiency={metrics.get('flow_efficiency', 'N/A')}%"
                )
            steps = org_value_stream_data.get("steps", [])
            if steps:
                step_summary = [s.get("step_name", "Unknown") for s in steps[:10]]
                context_parts.append(f"Organization's Process Steps: {', '.join(step_summary)}")

        if rag_context:
            context_parts.append(
                f"\n--- Organization Knowledge Base ---\n{rag_context}"
            )

        user_prompt = (
            "Generate detailed competitor operational benchmarks for this value stream:\n\n"
            + "\n".join(context_parts)
        )

        client = AsyncOpenAI()
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=3000,
        )

        content = response.choices[0].message.content
        result = json.loads(content)

        if "benchmarks" not in result:
            result["benchmarks"] = []
        if "industry_best_practices" not in result:
            result["industry_best_practices"] = []

        return result

    except Exception:
        return None
