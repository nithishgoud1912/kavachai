"""
KavachAI — Unit Tests: Data/Analytics Agent
Implements: Phase 5 DoD, FR-DAT-1..3, FR-SYN-3 ("LLM never does arithmetic")

Verifies:
- Pure pandas calculations (no LLM, no model_router)
- 2.1 -> 2.8 -> 3.7 mm/s yields +76% (+76.2%)
- Trend direction is INCREASING
- Threshold breach against 3.0 mm/s is True
"""

import pytest
import pandas as pd
from app.agents import data_agent
from app.agents.base import TrendDirection
from app.db.tabular_store import tabular_store


@pytest.fixture(autouse=True)
def setup_test_dataset():
    """Seed test dataset into tabular_store."""
    df = pd.DataFrame([
        {"timestamp": "2026-01-15T09:00:00Z", "equipment_id": "P-102", "metric": "vibration", "value": 2.1, "unit": "mm/s"},
        {"timestamp": "2026-04-18T09:00:00Z", "equipment_id": "P-102", "metric": "vibration", "value": 2.8, "unit": "mm/s"},
        {"timestamp": "2026-07-14T09:00:00Z", "equipment_id": "P-102", "metric": "vibration", "value": 3.7, "unit": "mm/s"},
    ])
    tabular_store.ingest_dataframe("test_p102", df)


def test_data_agent_deterministic_trend_and_pct_change():
    """Test deterministic trend calculation per FR-DAT-2."""
    result = data_agent.analyze(
        metric="vibration",
        equipment_id="P-102",
        dataset_id="test_p102",
        threshold=3.0,
    )

    # 1. Trend direction must be INCREASING
    assert result.trend == TrendDirection.INCREASING

    # 2. Percentage change: (3.7 - 2.1) / 2.1 = 76.2%
    assert result.pct_change == 76.2

    # 3. Threshold breach against 3.0 mm/s must be True (3.7 > 3.0)
    assert result.threshold_breach is True

    # 4. Underlying data points must match exactly 3 points
    assert len(result.data_points) == 3
    assert result.data_points[0].value == 2.1
    assert result.data_points[1].value == 2.8
    assert result.data_points[2].value == 3.7


def test_data_agent_nonexistent_equipment():
    """Test handling of equipment not in dataset."""
    result = data_agent.analyze(
        metric="vibration",
        equipment_id="NON_EXISTENT_PUMP",
        dataset_id="test_p102",
    )
    assert result.trend == TrendDirection.STABLE
    assert result.pct_change == 0.0
    assert result.data_points == []
    assert result.threshold_breach is None
