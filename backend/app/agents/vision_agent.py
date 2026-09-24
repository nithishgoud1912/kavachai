"""Image-grounded inspection; curated graph entries are never image observations."""
import json
from app.agents.base import VisionAnalysisResult
from app.db.object_store import object_store
from app.orchestrator.model_router import model_router

async def analyze_pid(pid_source_id, equipment_id):
    raw = object_store.get_raw_file(pid_source_id)
    if not raw: return VisionAnalysisResult(found=False)
    data, filename = raw
    pages = range(1, (object_store.get_page_count(pid_source_id) or 1)+1) if filename.lower().endswith('.pdf') else [1]
    for page in pages:
        image = object_store.get_file_page(pid_source_id, page) if filename.lower().endswith('.pdf') else data
        if not image: raise ValueError(f"Cannot render page {page}")
        response = await model_router.generate_vision(
            prompt=f"Locate equipment {equipment_id} on this image. Return JSON: found (boolean), connections (directly connected equipment tags), confidence (0 to 1), bounding_box (ymin,xmin,ymax,xmax in 0..1000 or null), visual_description. Report only visible facts. Do not infer hidden topology or recommend operational actions.",
            image_bytes=image, format='json')
        result = VisionAnalysisResult(**json.loads(response))
        if not 0 <= result.confidence <= 1: raise ValueError("Invalid visual confidence")
        if result.bounding_box and (len(result.bounding_box)!=4 or any(v<0 or v>1000 for v in result.bounding_box)):
            raise ValueError("Invalid bounding box")
        if result.found:
            result.visual_description = f"Page {page}: {result.visual_description or ''}"
            return result
    return VisionAnalysisResult(found=False, confidence=0)

async def get_connection_chain(equipment_id):
    return []  # No document-scoped topology was supplied.
