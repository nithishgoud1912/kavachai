"""Backend network-policy integration; this does not certify deployment air-gapping."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.database import init_db

@pytest.mark.asyncio
async def test_network_observation_does_not_masquerade_as_certification():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app),base_url='http://test') as client:
        assert (await client.get('/api/v1/network-monitor')).status_code==401
        session=(await client.post('/api/v1/session',json={'name':'Observer','department':'Security'})).json()['session_id']
        result=await client.get('/api/v1/network-monitor',headers={'Authorization':f'Bearer {session}'})
        assert result.status_code==200
        assert result.json()['verified_airgap'] is False
        assert 'scope' in result.json()
