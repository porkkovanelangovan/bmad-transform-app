"""
Process Parser — Parse visual process maps (images, PDFs) via OpenAI Vision
and BPMN 2.0 XML files into value stream steps.
"""

import base64
import json
import logging
import os
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

VISION_PROMPT = """Extract process steps from this process map / flowchart image.
Return ONLY valid JSON with this structure:
{"steps": [{"step_order": 1, "step_name": "...", "description": "...",
  "step_type": "trigger|process|decision|delivery",
  "process_time_hours": 0, "wait_time_hours": 0, "resources": "...",
  "is_bottleneck": false, "notes": "..."}]}

Rules:
- step_type must be one of: trigger, process, decision, delivery
- The first step should usually be "trigger" and last step "delivery"
- Estimate process_time_hours and wait_time_hours if any timing info is visible, otherwise use 0
- Set is_bottleneck to true for steps that appear to be bottlenecks
- Include ALL steps visible in the diagram
"""

TEXT_EXTRACTION_PROMPT = """Extract process/workflow steps from this PDF text content.
Return ONLY valid JSON with this structure:
{"steps": [{"step_order": 1, "step_name": "...", "description": "...",
  "step_type": "trigger|process|decision|delivery",
  "process_time_hours": 0, "wait_time_hours": 0, "resources": "...",
  "is_bottleneck": false, "notes": "..."}]}

Rules:
- step_type must be one of: trigger, process, decision, delivery
- The first step should usually be "trigger" and last step "delivery"
- Estimate times from the text if possible, otherwise use 0

Text content:
"""

# BPMN 2.0 namespace
BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
NS = {"bpmn": BPMN_NS}

# Map BPMN element types to step_type
BPMN_TYPE_MAP = {
    "startEvent": "trigger",
    "endEvent": "delivery",
    "exclusiveGateway": "decision",
    "inclusiveGateway": "decision",
    "parallelGateway": "decision",
    "task": "process",
    "userTask": "process",
    "serviceTask": "process",
    "scriptTask": "process",
    "manualTask": "process",
    "sendTask": "process",
    "receiveTask": "process",
    "businessRuleTask": "process",
    "subProcess": "process",
    "callActivity": "process",
}


def is_vision_available() -> bool:
    """Check if OpenAI API key is set for Vision API calls."""
    return bool(os.getenv("OPENAI_API_KEY", ""))


async def parse_process_image(file_bytes: bytes, filename: str, content_type: str) -> dict:
    """
    Parse an image or PDF into value stream steps using OpenAI Vision or text extraction.
    Returns {"steps": [...]} or {"error": "..."}.
    """
    is_pdf = filename.lower().endswith(".pdf") or content_type == "application/pdf"

    if is_pdf:
        return await _parse_pdf(file_bytes, filename)
    else:
        return await _parse_image(file_bytes, content_type)


async def _parse_image(file_bytes: bytes, content_type: str) -> dict:
    """Send image to OpenAI Vision API for step extraction."""
    if not is_vision_available():
        return {"error": "OpenAI API key not configured. Set OPENAI_API_KEY to enable Vision parsing."}

    from openai import AsyncOpenAI

    client = AsyncOpenAI()

    b64 = base64.b64encode(file_bytes).decode("utf-8")
    media_type = content_type or "image/png"

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": VISION_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{b64}",
                                "detail": "high",
                            },
                        },
                    ],
                }
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
        return {"steps": result.get("steps", [])}

    except json.JSONDecodeError as e:
        logger.error("Failed to parse Vision API response as JSON: %s", e)
        return {"error": f"AI returned invalid JSON: {e}", "raw_response": raw}
    except Exception as e:
        logger.error("Vision API call failed: %s", e)
        return {"error": f"Vision API error: {e}"}


async def _parse_pdf(file_bytes: bytes, filename: str) -> dict:
    """
    Parse PDF: try to render first page as image for Vision,
    fall back to text extraction + chat API.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return {"error": "PyMuPDF not installed. Run: pip install PyMuPDF"}

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        return {"error": f"Failed to open PDF: {e}"}

    if doc.page_count == 0:
        return {"error": "PDF has no pages"}

    # Try Option B first: render first page as image for Vision
    if is_vision_available():
        try:
            page = doc[0]
            # Render at 2x resolution for better OCR
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_bytes = pix.tobytes("png")
            result = await _parse_image(img_bytes, "image/png")
            if result.get("steps"):
                doc.close()
                return result
        except Exception as e:
            logger.warning("PDF image rendering failed, trying text extraction: %s", e)

    # Option A: extract text and send to chat API
    text = ""
    for page_num in range(min(doc.page_count, 5)):  # First 5 pages max
        text += doc[page_num].get_text()
    doc.close()

    text = text.strip()
    if not text:
        return {"error": "PDF contains no extractable text and image rendering failed."}

    # Truncate to fit context
    text = text[:8000]

    if not is_vision_available():
        return {
            "error": "OpenAI API key not configured. Set OPENAI_API_KEY for AI parsing.",
            "raw_text": text[:2000],
            "steps": [],
        }

    from openai import AsyncOpenAI

    client = AsyncOpenAI()

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": TEXT_EXTRACTION_PROMPT + text}
            ],
            max_tokens=4000,
            temperature=0.1,
        )

        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

        result = json.loads(raw)
        return {"steps": result.get("steps", [])}

    except Exception as e:
        logger.error("PDF text extraction via AI failed: %s", e)
        return {"error": f"AI extraction error: {e}", "raw_text": text[:2000], "steps": []}


def parse_bpmn(xml_bytes: bytes) -> dict:
    """
    Parse BPMN 2.0 XML into value stream steps.
    Follows sequence flow chain from startEvent to order steps.
    Returns {"steps": [...]}.
    """
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        return {"error": f"Invalid XML: {e}"}

    # Find the process element
    process = root.find(f"bpmn:process", NS)
    if process is None:
        # Try without namespace prefix
        process = root.find(f"{{{BPMN_NS}}}process")
    if process is None:
        # Try to find any process element
        for child in root.iter():
            if child.tag.endswith("}process") or child.tag == "process":
                process = child
                break
    if process is None:
        return {"error": "No BPMN process element found in XML"}

    # Collect all flow elements by ID
    elements = {}
    for elem_type, step_type in BPMN_TYPE_MAP.items():
        for elem in process.iter(f"{{{BPMN_NS}}}{elem_type}"):
            elem_id = elem.get("id", "")
            elem_name = elem.get("name", elem_type)
            elements[elem_id] = {
                "id": elem_id,
                "name": elem_name,
                "step_type": step_type,
                "bpmn_type": elem_type,
            }
        # Also try without namespace
        for elem in process.iter(elem_type):
            elem_id = elem.get("id", "")
            if elem_id not in elements:
                elem_name = elem.get("name", elem_type)
                elements[elem_id] = {
                    "id": elem_id,
                    "name": elem_name,
                    "step_type": step_type,
                    "bpmn_type": elem_type,
                }

    if not elements:
        return {"error": "No BPMN flow elements found in process"}

    # Build sequence flow graph: source -> [targets]
    flow_graph = {}
    for flow in process.iter(f"{{{BPMN_NS}}}sequenceFlow"):
        src = flow.get("sourceRef", "")
        tgt = flow.get("targetRef", "")
        if src:
            flow_graph.setdefault(src, []).append(tgt)
    # Also try without namespace
    for flow in process.iter("sequenceFlow"):
        src = flow.get("sourceRef", "")
        tgt = flow.get("targetRef", "")
        if src:
            flow_graph.setdefault(src, []).append(tgt)

    # Find start event(s)
    start_ids = [eid for eid, e in elements.items() if e["bpmn_type"] == "startEvent"]

    # Order steps by following sequence flow from start
    ordered_ids = []
    if start_ids and flow_graph:
        visited = set()
        queue = list(start_ids)
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            if current in elements:
                ordered_ids.append(current)
            for target in flow_graph.get(current, []):
                if target not in visited:
                    queue.append(target)
    else:
        # No sequence flows — just use elements in order they appeared
        ordered_ids = list(elements.keys())

    # Also add any elements not reached by flow
    for eid in elements:
        if eid not in ordered_ids:
            ordered_ids.append(eid)

    # Build steps list
    steps = []
    for order, eid in enumerate(ordered_ids, 1):
        elem = elements[eid]
        steps.append({
            "step_order": order,
            "step_name": elem["name"],
            "description": f"BPMN {elem['bpmn_type']} element",
            "step_type": elem["step_type"],
            "process_time_hours": 0,
            "wait_time_hours": 0,
            "resources": "",
            "is_bottleneck": False,
            "notes": f"BPMN type: {elem['bpmn_type']}",
        })

    return {"steps": steps}
