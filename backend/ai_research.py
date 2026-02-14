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


async def research_value_stream(
    segment_name: str,
    industry: str,
    org_name: str,
    org_context: dict,
    competitor_data: dict,
    sources_context: list[dict],
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
            '      "notes": "Comparative insight"\n'
            "    }\n"
            "  ]\n"
            "}\n\n"
            "Guidelines:\n"
            "- Include 6-10 steps covering the full end-to-end process\n"
            "- Use realistic time estimates based on industry data\n"
            "- Mark exactly one step as is_bottleneck: true\n"
            "- Include 2-4 competitor benchmarks\n"
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
