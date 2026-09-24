import pytest
from unittest.mock import patch, AsyncMock
from app.agents import vision_agent

@pytest.mark.asyncio
async def test_missing_image_never_uses_demo_graph():
    with patch.object(vision_agent.object_store,'get_raw_file',return_value=None):
        result=await vision_agent.analyze_pid('missing','P-102')
    assert result.found is False and result.confidence==0

@pytest.mark.asyncio
async def test_vision_reads_later_pdf_pages():
    with patch.object(vision_agent.object_store,'get_raw_file',return_value=(b'pdf','drawing.pdf')), patch.object(vision_agent.object_store,'get_page_count',return_value=2), patch.object(vision_agent.object_store,'get_file_page',return_value=b'image'), patch.object(vision_agent.model_router,'generate_vision',AsyncMock(side_effect=['{"found":false}','{"found":true,"connections":["B"],"confidence":0.8}'])) as generate:
        result=await vision_agent.analyze_pid('source','A')
    assert generate.call_count==2 and result.found and 'Page 2' in result.visual_description

@pytest.mark.asyncio
async def test_invalid_visual_bounds_rejected():
    with patch.object(vision_agent.object_store,'get_raw_file',return_value=(b'image','drawing.png')), patch.object(vision_agent.model_router,'generate_vision',AsyncMock(return_value='{"found":true,"bounding_box":[-1,0,10,20]}')):
        with pytest.raises(ValueError): await vision_agent.analyze_pid('source','A')
