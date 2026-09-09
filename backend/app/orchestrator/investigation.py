"""
KavachAI — Investigation Orchestrator
Implements: workflow.md §2 (Workflow B — Investigation Query),
            workflow.md §7 (Failure/Degradation Behavior),
            NFR-REL-2 (investigation continues server-side independent of SSE),
            NFR-PERF-3 (stream intermediate agent progress)

Runs Planner → specialist agents (parallel where possible) → Synthesis → Verification
Emits SSE agent_update events per API_Reference.md §4.
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import (
    AgentName, AgentStatus, CorpusSummary,
    EvidenceBundle, EvidenceItem, DocumentChunk,
    AgentUpdateEvent, SubTask, SpecChunk,
)
from app.agents import planner as planner_agent
from app.agents import document_agent
from app.agents import data_agent
from app.agents import vision_agent
from app.agents import rag_agent
from app.agents import synthesis as synthesis_agent
from app.agents import verification as verification_agent
from app.services.report_service import build_report
from app.db.sql_models import Investigation, Dataset
from app.config import settings

from sqlalchemy import select


class InvestigationRunner:
    """
    Orchestrates a full investigation pipeline.
    NFR-REL-2: Runs server-side independent of the SSE connection.
    """

    def __init__(self, investigation: Investigation, db: AsyncSession):
        self.investigation = investigation
        self.db = db
        self.events: list[dict] = []
        self._start_time = time.time()
        self.agents_invoked: list[str] = []
        self.attachments = getattr(self.investigation, "attachments", []) or []
        self.attachment_source_ids = [
            a.get("source_id") for a in self.attachments
            if isinstance(a, dict) and a.get("source_id")
        ]

    def _elapsed_ms(self) -> int:
        return int((time.time() - self._start_time) * 1000)

    def _emit(self, agent: str, status: str, message: str):
        """Record an SSE event."""
        event = {
            "agent": agent,
            "status": status,
            "message": message,
            "elapsed_ms": self._elapsed_ms(),
        }
        self.events.append(event)

    async def run(self) -> dict:
        """
        Execute the full investigation pipeline.
        Returns the final report dict or an insufficient_evidence result.

        Implements: workflow.md §2 (full Workflow B)
        """
        try:
            # --- 1. PLANNER (FR-PLN-1..3) ---
            if self.attachments:
                self._emit("planner", "working", f"Analyzing query and {len(self.attachments)} attached files/folders...")
            else:
                self._emit("planner", "working", "Analyzing query...")
            self.agents_invoked.append("planner")

            corpus_summary = await self._get_corpus_summary()
            plan = await planner_agent.plan(
                self.investigation.query,
                corpus_summary,
                attached_files=self.attachments,
            )

            # If user submitted attachments, guarantee in-scope status
            if self.attachments:
                plan.is_in_scope = True
                if not plan.sub_tasks:
                    plan.sub_tasks = [
                        SubTask(agent=AgentName.DOCUMENT_AGENT, goal=f"Analyze uploaded files for: {self.investigation.query}"),
                        SubTask(agent=AgentName.RAG_AGENT, goal=f"Find relevant specifications and limits in uploaded files"),
                    ]

            # Store plan
            self.investigation.plan = {
                "sub_tasks": [{"agent": st.agent.value, "goal": st.goal} for st in plan.sub_tasks],
                "is_in_scope": plan.is_in_scope,
            }
            self.investigation.status = "investigating"
            self.investigation.events = list(self.events)
            await self.db.commit()

            # FR-PLN-2: Out-of-scope check (Workflow E)
            if not plan.is_in_scope:
                self._emit("planner", "complete", "Query is out of scope")
                return await self._insufficient_evidence("No relevant evidence found in the knowledge base.")

            self._emit("planner", "complete",
                       f"Decomposed into {len(plan.sub_tasks)} sub-tasks")

            # --- 2. DISPATCH SPECIALIST AGENTS (parallel where possible) ---
            evidence_bundle = EvidenceBundle()
            evidence_items = []

            # Group sub-tasks by agent
            doc_tasks = [st for st in plan.sub_tasks if st.agent == AgentName.DOCUMENT_AGENT]
            data_tasks = [st for st in plan.sub_tasks if st.agent == AgentName.DATA_AGENT]
            vision_tasks = [st for st in plan.sub_tasks if st.agent == AgentName.VISION_AGENT]
            rag_tasks = [st for st in plan.sub_tasks if st.agent == AgentName.RAG_AGENT]

            # Run Document, Data, and Vision agents in parallel (workflow.md §2)
            parallel_tasks = []

            if doc_tasks:
                parallel_tasks.append(self._run_document_agent(doc_tasks, evidence_bundle, evidence_items))
            if data_tasks:
                parallel_tasks.append(self._run_data_agent(data_tasks, evidence_bundle, evidence_items))
            if vision_tasks:
                parallel_tasks.append(self._run_vision_agent(vision_tasks, evidence_bundle, evidence_items))
            elif self._extract_equipment_ids() and corpus_summary.pid_drawings > 0 and not self.attachments:
                parallel_tasks.append(self._run_vision_agent([SubTask(agent=AgentName.VISION_AGENT, goal=f"Identify {self._extract_equipment_ids()[0]} in P&ID")], evidence_bundle, evidence_items))

            if parallel_tasks:
                await asyncio.gather(*parallel_tasks, return_exceptions=True)

            # RAG runs after (or alongside — it's independent)
            if rag_tasks:
                await self._run_rag_agent(rag_tasks, evidence_bundle, evidence_items)

            evidence_bundle.evidence_items = evidence_items

            # --- 3. SYNTHESIS (FR-SYN-1..3) ---
            self._emit("synthesis", "working", "Synthesizing findings from evidence...")

            draft_findings = await synthesis_agent.synthesize(evidence_bundle)

            self._emit("synthesis", "complete",
                       f"Produced {len(draft_findings.findings)} draft findings")

            # --- 4. VERIFICATION (FR-VER-1..4) ---
            self._emit("verification_agent", "working", "Verifying findings against evidence...")
            self.agents_invoked.append("verification_agent")

            ver_result = await verification_agent.verify(draft_findings, evidence_bundle)

            # FR-VER-4: Check if zero supported findings
            supported_count = sum(
                1 for f in ver_result.findings
                if f.verification_status.value == "supported"
            )

            if supported_count == 0:
                self._emit("verification_agent", "complete", "No findings could be verified")
                return await self._insufficient_evidence(
                    "Evidence gathered but no findings could be verified."
                )

            self._emit("verification_agent", "complete",
                       f"Verified: {supported_count} supported findings, "
                       f"confidence {ver_result.overall_confidence}%")

            # --- 5. BUILD REPORT (FR-RPT-1) ---
            # Get P&ID chain if vision was used
            pid_chain = None
            if evidence_bundle.vision_findings and evidence_bundle.vision_findings.found:
                # Extract equipment_id from query context
                pid_chain = await self._get_pid_chain()
            elif self._extract_equipment_ids() and corpus_summary.pid_drawings > 0:
                pid_chain = await self._get_pid_chain()

            report = build_report(
                investigation_id=self.investigation.id,
                query=self.investigation.query,
                verification_result=ver_result,
                evidence_bundle=evidence_bundle,
                pid_chain=pid_chain,
            )

            # Store results
            self.investigation.status = "complete"
            self.investigation.report = report
            self.investigation.confidence = ver_result.overall_confidence
            self.investigation.verification_status = ver_result.overall_status
            self.investigation.evidence_bundle = evidence_bundle.model_dump()
            self.investigation.draft_findings = draft_findings.model_dump()
            self.investigation.events = list(self.events)
            self.investigation.completed_at = datetime.now(timezone.utc)
            await self.db.commit()

            return {"type": "investigation_complete", "report": report}

        except Exception as e:
            self.investigation.status = "failed"
            self.investigation.completed_at = datetime.now(timezone.utc)
            await self.db.commit()
            raise

    async def _run_document_agent(self, tasks, bundle, evidence_items):
        """Run document agent sub-tasks. Implements: FR-DOC-1..3"""
        try:
            self._emit("document_agent", "working", "Searching documents...")
            self.agents_invoked.append("document_agent")

            all_chunks = []
            att_map = {
                a.get("source_id"): (a.get("path") or a.get("filename") or "Uploaded Document")
                for a in self.attachments if isinstance(a, dict) and a.get("source_id")
            }

            for task in tasks:
                # Retrieve with equipment and source_id filters
                filters = {"equipment_ids": self._extract_equipment_ids()}
                if self.attachment_source_ids:
                    filters["source_ids"] = self.attachment_source_ids

                chunks = await document_agent.retrieve(
                    sub_task_goal=task.goal,
                    filters=filters,
                    n_results=6,
                )
                all_chunks.extend(chunks)

                # If attachments exist, also retrieve directly from the uploaded files
                if self.attachment_source_ids:
                    att_chunks = await document_agent.retrieve(
                        sub_task_goal=task.goal,
                        filters={"source_ids": self.attachment_source_ids},
                        n_results=6,
                    )
                    seen_chunks = {c.chunk_text for c in all_chunks}
                    for ac in att_chunks:
                        if ac.chunk_text not in seen_chunks:
                            all_chunks.append(ac)
                            seen_chunks.add(ac.chunk_text)

            bundle.document_findings = all_chunks

            for chunk in all_chunks:
                label = att_map.get(chunk.source_id, "Document")
                evidence_items.append(EvidenceItem(
                    type="document",
                    source_id=chunk.source_id,
                    label=label,
                    page=chunk.page,
                ))

            self._emit("document_agent", "complete",
                       f"Found {len(all_chunks)} relevant passages")

        except Exception as e:
            # NFR-REL-2: Degrade gracefully
            self._emit("document_agent", "failed", f"Document search failed: {str(e)[:100]}")

    async def _run_data_agent(self, tasks, bundle, evidence_items):
        """Run data agent sub-tasks. Implements: FR-DAT-1..3"""
        try:
            self._emit("data_agent", "working", "Analyzing operational data...")
            self.agents_invoked.append("data_agent")

            # Find the dataset
            result = await self.db.execute(select(Dataset).where(Dataset.status == "ready"))
            dataset = result.scalar_one_or_none()

            if not dataset:
                # workflow.md §7: Data Agent no-rows → drop data sub-finding
                self._emit("data_agent", "skipped", "No dataset available")
                return

            equipment_ids = self._extract_equipment_ids()
            equip_id = equipment_ids[0] if equipment_ids else "P-102"

            # Dynamically derive metric from subtask goals, query, or dataset schema
            combined_text = (self.investigation.query + " " + " ".join(t.goal for t in tasks)).lower()
            metric = "vibration"
            metric_candidates = ["vibration", "temperature", "temp", "pressure", "flow", "current", "voltage", "rpm", "speed", "power"]
            for candidate in metric_candidates:
                if candidate in combined_text:
                    metric = "temperature" if candidate == "temp" else candidate
                    break
            else:
                if dataset.table_name:
                    available_metrics = tabular_store.get_distinct_metrics(dataset.table_name, equip_id)
                    if available_metrics:
                        metric = available_metrics[0]

            # Run analysis (pure pandas — no LLM)
            analysis = data_agent.analyze(
                metric=metric,
                equipment_id=equip_id,
                dataset_id=dataset.id,
            )

            if analysis.data_points:
                bundle.data_findings = analysis
                evidence_items.append(EvidenceItem(
                    type="dataset",
                    source_id=dataset.id,
                    label="Operating Data",
                ))

                self._emit("data_agent", "complete",
                           f"Computed trend: {analysis.trend.value} ({analysis.pct_change:+.0f}%)")
            else:
                self._emit("data_agent", "skipped", "No data found for this equipment")

        except Exception as e:
            self._emit("data_agent", "failed", f"Data analysis failed: {str(e)[:100]}")

    async def _run_vision_agent(self, tasks, bundle, evidence_items):
        """Run vision agent sub-tasks. Implements: FR-VIS-1..3"""
        try:
            self._emit("vision_agent", "working", "Analyzing P&ID...")
            self.agents_invoked.append("vision_agent")

            equipment_ids = self._extract_equipment_ids()
            equip_id = equipment_ids[0] if equipment_ids else "P-102"

            result = await vision_agent.analyze_pid(
                pid_source_id="pid_demo",  # Pre-computed fallback
                equipment_id=equip_id,
            )

            if result.found:
                bundle.vision_findings = result
                evidence_items.append(EvidenceItem(
                    type="pid_drawing",
                    source_id="pid_demo",
                    label="P&ID Drawing",
                ))
                self._emit("vision_agent", "complete",
                           f"Found {equip_id}, connected to: {', '.join(result.connections)}")
            else:
                # FR-VIS-3: Graceful degradation
                self._emit("vision_agent", "skipped",
                           f"Equipment {equip_id} not found in P&ID")

        except asyncio.TimeoutError:
            # workflow.md §7: Vision Agent timeout → continue without P&ID
            self._emit("vision_agent", "failed", "P&ID analysis timed out")
        except Exception as e:
            self._emit("vision_agent", "failed", f"P&ID analysis failed: {str(e)[:100]}")

    async def _run_rag_agent(self, tasks, bundle, evidence_items):
        """Run RAG agent sub-tasks. Implements: FR-RAG-1..2"""
        try:
            self._emit("rag_agent", "working", "Retrieving specifications...")
            self.agents_invoked.append("rag_agent")

            equipment_ids = self._extract_equipment_ids()
            equip_id = equipment_ids[0] if equipment_ids else "P-102"

            all_specs = []
            att_map = {
                a.get("source_id"): (a.get("path") or a.get("filename") or "Uploaded Spec")
                for a in self.attachments if isinstance(a, dict) and a.get("source_id")
            }

            for task in tasks:
                specs = await rag_agent.retrieve_spec(
                    query=task.goal,
                    equipment_id=equip_id,
                )
                all_specs.extend(specs)

                # Also search attached sources for relevant specifications
                if self.attachment_source_ids:
                    att_chunks = await document_agent.retrieve(
                        sub_task_goal=f"specification threshold limit {task.goal}",
                        filters={"source_ids": self.attachment_source_ids},
                        n_results=3,
                    )
                    for ac in att_chunks:
                        all_specs.append(SpecChunk(
                            chunk_text=ac.chunk_text,
                            source_id=ac.source_id,
                            page=ac.page,
                            section=None,
                        ))

            bundle.spec_findings = all_specs

            for spec in all_specs:
                label = att_map.get(spec.source_id, "Specification")
                evidence_items.append(EvidenceItem(
                    type="document",
                    source_id=spec.source_id,
                    label=label,
                    page=spec.page,
                    section=spec.section,
                ))

            self._emit("rag_agent", "complete",
                       f"Retrieved {len(all_specs)} specification passages")

        except Exception as e:
            self._emit("rag_agent", "failed", f"Spec retrieval failed: {str(e)[:100]}")

    async def _get_corpus_summary(self) -> CorpusSummary:
        """Build corpus summary for the planner."""
        from app.db.sql_models import Document, Dataset as DatasetModel
        from sqlalchemy import func

        doc_count = (await self.db.execute(
            select(func.count(Document.id)).where(Document.status == "ready")
        )).scalar() or 0

        ds_count = (await self.db.execute(
            select(func.count(DatasetModel.id)).where(DatasetModel.status == "ready")
        )).scalar() or 0

        pid_count = (await self.db.execute(
            select(func.count(Document.id)).where(
                Document.status == "ready",
                Document.document_type == "pid_drawing",
            )
        )).scalar() or 0

        if self.attachments:
            doc_count += len(self.attachments)

        return CorpusSummary(
            documents=doc_count,
            datasets=ds_count,
            pid_drawings=pid_count,
        )

    def _extract_equipment_ids(self) -> list[str]:
        """Extract equipment IDs mentioned in the query."""
        import re
        pattern = re.compile(r"\b([A-Z]-\d{2,4})\b")
        return pattern.findall(self.investigation.query)

    async def _get_pid_chain(self) -> Optional[list[str]]:
        """Get the P&ID connection chain for the primary equipment."""
        equipment_ids = self._extract_equipment_ids()
        if equipment_ids:
            return await vision_agent.get_connection_chain(equipment_ids[0])
        return None

    async def _insufficient_evidence(self, message: str) -> dict:
        """Handle the insufficient_evidence terminal state."""
        self.investigation.status = "insufficient_evidence"
        self.investigation.events = list(self.events)
        self.investigation.completed_at = datetime.now(timezone.utc)
        await self.db.commit()

        return {
            "type": "insufficient_evidence",
            "investigation_id": self.investigation.id,
            "message": message,
        }
