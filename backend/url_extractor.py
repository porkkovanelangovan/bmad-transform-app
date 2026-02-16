"""
URL Extractor — Fetch a URL, scrape its content, and use AI to extract
process/workflow data as value stream steps.
"""

import json
import logging
import os

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

EXTRACTION_PROMPT = """Extract process/workflow steps from this web page content.
If the content describes a business process, workflow, or value stream, extract structured steps.
Return ONLY valid JSON with this structure:
{"steps": [{"step_order": 1, "step_name": "...", "description": "...",
  "step_type": "trigger|process|decision|delivery",
  "process_time_hours": 0, "wait_time_hours": 0, "resources": "...",
  "is_bottleneck": false, "notes": "..."}],
 "confidence": "high|medium|low"}

Rules:
- confidence should be "high" if the content clearly describes a process, "medium" if it's somewhat process-related, "low" if it's a stretch
- If no process/workflow steps can be identified, return {"steps": [], "confidence": "low"}
- step_type must be one of: trigger, process, decision, delivery

Web page content:
"""


async def extract_from_url(url: str) -> dict:
    """
    Fetch URL content, extract text, and use AI to identify process steps.
    Returns {steps, source_url, confidence, raw_text_preview} or {error}.
    """
    # Fetch the page
    try:
        async with httpx.AsyncClient(
            timeout=30, follow_redirects=True, verify=True
        ) as client:
            resp = await client.get(
                url,
                headers={"User-Agent": USER_AGENT},
            )
            resp.raise_for_status()
            html = resp.text
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP {e.response.status_code} fetching URL: {url}"}
    except Exception as e:
        return {"error": f"Failed to fetch URL: {e}"}

    # Extract text from HTML
    soup = BeautifulSoup(html, "html.parser")

    # Remove script and style elements
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    # Extract meaningful text from specific elements
    text_parts = []
    for tag in soup.find_all(["p", "li", "td", "th", "h1", "h2", "h3", "h4", "h5", "h6"]):
        text = tag.get_text(strip=True)
        if text and len(text) > 5:
            text_parts.append(text)

    extracted_text = "\n".join(text_parts)

    if not extracted_text.strip():
        # Fallback: get all text
        extracted_text = soup.get_text(separator="\n", strip=True)

    if not extracted_text.strip():
        return {"error": "No text content found at URL", "source_url": url}

    # Truncate to fit in context
    extracted_text = extracted_text[:8000]
    raw_preview = extracted_text[:500]

    # Check for OpenAI availability
    if not os.getenv("OPENAI_API_KEY"):
        return {
            "steps": [],
            "source_url": url,
            "confidence": "low",
            "raw_text_preview": raw_preview,
            "note": "OpenAI API key not configured. Showing raw text only.",
        }

    # Send to OpenAI for extraction
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI()

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": EXTRACTION_PROMPT + extracted_text}
            ],
            max_tokens=4000,
            temperature=0.1,
        )

        raw = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

        result = json.loads(raw)
        return {
            "steps": result.get("steps", []),
            "source_url": url,
            "confidence": result.get("confidence", "medium"),
            "raw_text_preview": raw_preview,
        }

    except json.JSONDecodeError as e:
        logger.error("Failed to parse AI response as JSON: %s", e)
        return {
            "error": f"AI returned invalid JSON: {e}",
            "steps": [],
            "source_url": url,
            "confidence": "low",
            "raw_text_preview": raw_preview,
        }
    except Exception as e:
        logger.error("AI extraction from URL failed: %s", e)
        return {
            "error": f"AI extraction error: {e}",
            "steps": [],
            "source_url": url,
            "confidence": "low",
            "raw_text_preview": raw_preview,
        }
