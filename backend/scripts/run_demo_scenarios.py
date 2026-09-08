"""
KavachAI — Demo Scenario Runner & Fixture Generator
Implements: Phase 16 (Demo Rehearsal Artifacts), PRD §9 (Risk Mitigation),
            workflow.md §6 (Demo Script Mapping), NFR-PERF-1/2, NFR-REL-1

Pre-runs the 3 core demo scenarios:
  1. "What should an employee do during a fire emergency?" (RAG-only, NFR-PERF-2 <10s)
  2. "Investigate Pump P-102 and determine whether its condition has deteriorated." (Multi-agent, NFR-PERF-1 <45s)
  3. "What is the current price of crude oil?" (Workflow E — Out-of-scope, Refusal)

Caches output into tests/fixtures/ for demo reliability.
"""

import os
import sys
import time
import json
import asyncio
from pathlib import Path
from datetime import datetime, timezone

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.database import init_db, async_session
from app.db.sql_models import Investigation, Session as SessionModel
from app.orchestrator.investigation import InvestigationRunner


FIXTURES_DIR = Path("./tests/fixtures")
FIXTURES_DIR.mkdir(parents=True, exist_ok=True)


DEMO_SCENARIOS = [
    {
        "id": "scenario_1_fire_emergency",
        "name": "Scenario 1: Fire Emergency SOP",
        "query": "What should an employee do during a fire emergency?",
        "user_name": "Priya",
        "department": "HSE",
        "max_latency_sec": 10.0,  # NFR-PERF-2
        "expected_status": "complete",
        "expected_finding": "evacuate",
    },
    {
        "id": "scenario_2_pump_p102",
        "name": "Scenario 2: Pump P-102 Deterioration Investigation",
        "query": "Investigate Pump P-102 and determine whether its condition has deteriorated.",
        "user_name": "Vikram",
        "department": "Reliability Engineering",
        "max_latency_sec": 45.0,  # NFR-PERF-1
        "expected_status": "complete",
        "expected_finding": "vibration",
    },
    {
        "id": "scenario_3_out_of_scope",
        "name": "Scenario 3: Out-of-Scope Hallucination Refusal",
        "query": "What is the current price of crude oil?",
        "user_name": "Rajesh",
        "department": "Finance",
        "max_latency_sec": 5.0,
        "expected_status": "insufficient_evidence",
        "expected_finding": None,
    },
]


async def run_scenario(scenario: dict) -> dict:
    """Run a single demo scenario and validate requirements."""
    print(f"\nRunning {scenario['name']}...")
    print(f"  Query: \"{scenario['query']}\"")
    print(f"  User: {scenario['user_name']} ({scenario['department']})")

    async with async_session() as db:
        # Create session
        session = SessionModel(name=scenario["user_name"], department=scenario["department"])
        db.add(session)
        await db.commit()
        await db.refresh(session)

        # Create investigation
        investigation = Investigation(
            query=scenario["query"],
            session_id=session.id,
            status="planning",
        )
        db.add(investigation)
        await db.commit()
        await db.refresh(investigation)

        # Time the investigation
        start_time = time.time()
        runner = InvestigationRunner(investigation, db)
        result = await runner.run()
        elapsed_sec = time.time() - start_time

        # Refresh investigation record
        await db.refresh(investigation)

        # Validate status
        status_matches = (investigation.status == scenario["expected_status"])
        latency_ok = (elapsed_sec <= scenario["max_latency_sec"])

        print(f"  Result status: {investigation.status} (Expected: {scenario['expected_status']}) -> {'PASS' if status_matches else 'FAIL'}")
        print(f"  Latency: {elapsed_sec:.2f}s (Budget: <{scenario['max_latency_sec']}s) -> {'PASS' if latency_ok else 'WARN'}")
        print(f"  Timeline events: {len(runner.events)} emitted")

        # Cache fixture
        fixture_data = {
            "scenario_id": scenario["id"],
            "name": scenario["name"],
            "query": scenario["query"],
            "status": investigation.status,
            "elapsed_sec": round(elapsed_sec, 2),
            "timeline_events": runner.events,
            "report": investigation.report,
            "confidence": investigation.confidence,
            "verification_status": investigation.verification_status,
            "plan": investigation.plan,
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }

        fixture_file = FIXTURES_DIR / f"{scenario['id']}.json"
        with open(fixture_file, "w", encoding="utf-8") as f:
            json.dump(fixture_data, f, indent=2)

        print(f"  [SAVED] Fixture cached at {fixture_file}")

        return {
            "scenario": scenario["id"],
            "passed": status_matches and latency_ok,
            "status": investigation.status,
            "elapsed_sec": elapsed_sec,
            "events_count": len(runner.events),
        }


async def main():
    print("=" * 65)
    print("KavachAI — Demo Scenarios Rehearsal & Fixture Caching (Phase 16)")
    print("=" * 65)

    await init_db()

    results = []
    for sc in DEMO_SCENARIOS:
        res = await run_scenario(sc)
        results.append(res)

    print("\n" + "=" * 65)
    print("Rehearsal Summary:")
    all_passed = True
    for r in results:
        status_str = "[PASS]" if r["passed"] else "[FAIL]"
        print(f"  {status_str} {r['scenario']}: status={r['status']}, time={r['elapsed_sec']:.2f}s, events={r['events_count']}")
        if not r["passed"]:
            all_passed = False

    print("=" * 65)
    if all_passed:
        print("Phase 16 DoD: ALL 3 DEMO SCENARIOS PASSED AND CACHED!")
    else:
        print("Phase 16 DoD: SOME SCENARIOS FAILED OR EXCEEDED LATENCY BUDGET")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
