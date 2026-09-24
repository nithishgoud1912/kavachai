"""Retrieval policy at the embedding/vector service boundary."""
import pytest
from unittest.mock import AsyncMock, patch
from app.agents import document_agent

@pytest.mark.asyncio
async def test_document_agent_filters_identity_and_relevance():
    results=[dict(chunk_text='Relevant inspection',source_id='allowed',page=2,score=.9),
             dict(chunk_text='Private',source_id='forbidden',page=1,score=.99),
             dict(chunk_text='Unrelated',source_id='allowed',page=1,score=.01)]
    with patch.object(document_agent.model_router,'embed',AsyncMock(return_value=[[.1]*768])), patch.object(document_agent.vector_store,'query',return_value=results):
        chunks=await document_agent.retrieve('inspection',{'source_ids':['allowed']})
    assert len(chunks)==1 and chunks[0].page==2 and chunks[0].source_id=='allowed'

@pytest.mark.asyncio
async def test_missing_scope_never_searches_global_corpus():
    with patch.object(document_agent.model_router,'embed',AsyncMock()) as embed:
        assert await document_agent.retrieve('anything',{})==[]
        embed.assert_not_called()
