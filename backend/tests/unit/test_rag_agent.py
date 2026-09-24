import pytest
from unittest.mock import AsyncMock, patch
from app.agents import rag_agent
from app.agents.base import DocumentChunk

@pytest.mark.asyncio
async def test_spec_retrieval_keeps_authorized_source_and_section():
    chunks=[DocumentChunk(chunk_text='Section 4.2: limit 3.0 mm/s',source_id='manual',page=2,score=.9)]
    with patch('app.agents.document_agent.retrieve',AsyncMock(return_value=chunks)) as retrieve:
        result=await rag_agent.retrieve_spec('limit','P-102',{'source_ids':['manual']})
        assert retrieve.call_args.args[1]=={'source_ids':['manual']}
    assert result[0].source_id=='manual' and result[0].section=='4.2'
