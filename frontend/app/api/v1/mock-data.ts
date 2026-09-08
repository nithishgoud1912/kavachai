import type {
  KnowledgeBaseSummary,
  InvestigationPlan,
  Report,
  EvidenceSource,
  AuditEntry,
} from "@/app/types";

export const mockSummary: KnowledgeBaseSummary = {
  documents: 7,
  datasets: 1,
  pid_drawings: 1,
};

export const mockDefaultPlan: InvestigationPlan = {
  investigation_id: "inv_7788",
  sub_tasks: [
    { agent: "document_agent", goal: "Find inspection reports mentioning P-102" },
    { agent: "data_agent", goal: "Compute vibration trend for P-102, Jan–Jul" },
    { agent: "vision_agent", goal: "Identify P-102 connectivity in P&ID" },
    { agent: "rag_agent", goal: "Retrieve operating threshold for this pump model" },
  ],
};

export const mockDefaultReport: Report = {
  investigation_id: "inv_7788",
  query: "Investigate Pump P-102 and determine whether its condition has deteriorated.",
  overall_status: "attention_required",
  condition_summary: "Potential deterioration detected",
  findings: [
    {
      id: "f1",
      title: "Increasing vibration",
      detail: "Jan 2.1 → Apr 2.8 → Jul 3.7 mm/s (+76%)",
      verification_status: "supported",
      evidence: [
        { type: "document", source_id: "doc_1120", label: "Inspection Report (Jan)", page: 4 },
        { type: "document", source_id: "doc_1121", label: "Inspection Report (Apr)", page: 12 },
        { type: "document", source_id: "doc_1122", label: "Inspection Report (Jul)", page: 17 },
        { type: "dataset", source_id: "ds_4471", label: "Vibration Sensor Telemetry" },
      ],
    },
    {
      id: "f2",
      title: "Exceeds attention threshold",
      detail: "Current 3.7 mm/s > spec 3.0 mm/s",
      verification_status: "supported",
      evidence: [
        { type: "document", source_id: "doc_1130", label: "Pump Operating Manual", page: null, section: "4.2" },
      ],
    },
    {
      id: "f3",
      title: "Process Connectivity Verified",
      detail: "Upstream Tank T-101 feeds P-102, discharge to Valve V-204 and Reactor R-101",
      verification_status: "supported",
      evidence: [
        { type: "pid_drawing", source_id: "pid_2201", label: "Refinery P&ID Dwg Rev 4" },
      ],
    },
  ],
  pid_relationship: ["T-101", "P-102", "V-204", "R-101"],
  conclusion:
    "The available evidence indicates that P-102's condition has deteriorated over the observed period. Engineering inspection is recommended. The evidence does NOT establish imminent failure.",
  confidence: 91,
  verification_status: "verified",
  generated_at: new Date().toISOString(),
};

export const mockEvidenceMap: Record<string, EvidenceSource> = {
  doc_1120: {
    source_id: "doc_1120",
    type: "document",
    filename: "P-102_Inspection_Jan.pdf",
    page: 4,
    excerpt:
      "Pump P-102 quarterly check. Peak vibration measured at 2.1 mm/s RMS. Bearings normal, operating temperature 62°C. Within normal baseline range.",
    view_url: "/files/doc_1120/page/4",
  },
  doc_1121: {
    source_id: "doc_1121",
    type: "document",
    filename: "P-102_Inspection_Apr.pdf",
    page: 12,
    excerpt:
      "Routine inspection of P-102. Vibration level rose to 2.8 mm/s RMS. Slight acoustic anomaly detected on non-drive end bearing. Lubrication replenished.",
    view_url: "/files/doc_1121/page/12",
  },
  doc_1122: {
    source_id: "doc_1122",
    type: "document",
    filename: "P-102_Inspection_July.pdf",
    page: 17,
    excerpt:
      "Pump P-102 — Vibration: 3.7 mm/s. Temperature: 77°C. Status: Abnormal. Exceeds operational advisory limit of 3.0 mm/s. Immediate maintenance review recommended.",
    view_url: "/files/doc_1122/page/17",
  },
  doc_1130: {
    source_id: "doc_1130",
    type: "document",
    filename: "P-100_Series_Operating_Manual.pdf",
    page: 28,
    excerpt:
      "Section 4.2: Vibration Criteria — Normal continuous operation: < 2.5 mm/s RMS. Advisory attention threshold: 3.0 mm/s RMS. Critical trip shutdown: 4.5 mm/s RMS.",
    view_url: "/files/doc_1130/section/4.2",
  },
  ds_4471: {
    source_id: "ds_4471",
    type: "dataset",
    rows: [
      { timestamp: "2026-01-10", equipment_id: "P-102", metric: "vibration", value: 2.1, unit: "mm/s" },
      { timestamp: "2026-04-11", equipment_id: "P-102", metric: "vibration", value: 2.8, unit: "mm/s" },
      { timestamp: "2026-07-09", equipment_id: "P-102", metric: "vibration", value: 3.7, unit: "mm/s" },
    ],
  },
  pid_2201: {
    source_id: "pid_2201",
    type: "pid_drawing",
    filename: "Refinery_Plant_PID.pdf",
    highlighted_component: "P-102",
    connections: ["T-101", "V-204", "R-101"],
    view_url: "/files/pid_2201/annotated",
  },
};

export const mockAuditEntries: AuditEntry[] = [
  {
    investigation_id: "inv_7788",
    user: "Abhinay Boya",
    department: "HSE",
    query: "Investigate Pump P-102 and determine whether its condition has deteriorated.",
    agents_invoked: ["planner", "document_agent", "data_agent", "vision_agent", "rag_agent", "verification_agent"],
    verification_status: "verified",
    confidence: 91,
    timestamp: new Date().toISOString(),
  },
];
