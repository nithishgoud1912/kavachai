import type {
  KnowledgeBaseSummary,
  InvestigationPlan,
  Report,
  EvidenceSource,
  AuditEntry,
  InvestigationSummary,
  Conversation,
  ChatMessage,
  ChatAttachment,
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

// ─── Investigation Summaries for Sidebar & List ─────────────────────

export const mockInvestigationSummaries: InvestigationSummary[] = [
  {
    id: "inv_7788",
    query: "Investigate Pump P-102 and determine whether its condition has deteriorated.",
    status: "complete",
    condition_summary: "Potential deterioration detected",
    confidence: 91,
    verification_status: "verified",
    created_at: new Date(Date.now() - 3600000).toISOString(),
    completed_at: new Date(Date.now() - 3500000).toISOString(),
  },
];

// ─── Chat Conversations & Messages Store ────────────────────────────

export const mockConversations: Conversation[] = [];
export const mockConversationMessages: Record<string, ChatMessage[]> = {};

// ─── Uploaded Chat Files Store ──────────────────────────────────────

export interface StoredChatFile {
  filename: string;
  url: string;
  type: "document" | "image";
  extracted_text: string;
  dataBase64?: string;
  contentType?: string;
}

export const mockChatFiles: Record<string, StoredChatFile> = {};

// ─── AI Response Generator (Offline / Demo Fallback) ────────────────

export function generateMockAssistantResponse(
  conversationType: "general" | "report" = "general",
  userQuery: string,
  attachments: ChatAttachment[] = [],
  investigationId?: string
): string {
  const queryLower = userQuery.toLowerCase();

  // 1. Report-grounded chat
  if (conversationType === "report" || investigationId) {
    if (queryLower.includes("key finding") || queryLower.includes("findings")) {
      return (
        "### Key Findings for Pump P-102\n\n" +
        "1. **Increasing Vibration (+76%)**: Vibration levels on the non-drive end bearing have progressively risen from **2.1 mm/s RMS (Jan)** to **2.8 mm/s (Apr)** and reached **3.7 mm/s (Jul)**. *(Status: Supported)*\n" +
        "2. **Exceeds Operational Advisory Threshold**: The current 3.7 mm/s reading exceeds the OEM advisory threshold of **3.0 mm/s RMS** defined in *Section 4.2 of the P-100 Series Operating Manual*. *(Status: Supported)*\n" +
        "3. **Process Connectivity**: Plant P&ID verified that P-102 takes suction from **Tank T-101** and discharges through **Control Valve V-204** to **Reactor R-101**. Any trip of P-102 directly impacts feed supply to R-101. *(Status: Supported)*\n\n" +
        "**Overall Condition**: *Attention Required* with 91% multi-agent confidence. Imminent catastrophic failure is not established, but preventative maintenance is warranted."
      );
    }
    if (queryLower.includes("evidence") || queryLower.includes("support")) {
      return (
        "### Grounded Evidence Sources\n\n" +
        "The conclusion is cross-verified by 4 independent data streams:\n" +
        "- **Document Evidence**:\n" +
        "  - `doc_1120`: *P-102_Inspection_Jan.pdf* (Page 4) — 2.1 mm/s baseline, normal lubrication.\n" +
        "  - `doc_1121`: *P-102_Inspection_Apr.pdf* (Page 12) — 2.8 mm/s, slight acoustic anomaly.\n" +
        "  - `doc_1122`: *P-102_Inspection_July.pdf* (Page 17) — 3.7 mm/s, abnormal temperature (77°C).\n" +
        "- **Sensor Telemetry (`ds_4471`)**: Vibration sensor trends confirm steady escalation.\n" +
        "- **OEM Specification (`doc_1130`)**: Normal continuous limit: <2.5 mm/s; Advisory limit: 3.0 mm/s; Critical trip: 4.5 mm/s.\n" +
        "- **P&ID Drawing (`pid_2201`)**: Confirms fluid flow chain `T-101 → P-102 → V-204 → R-101`."
      );
    }
    if (queryLower.includes("recommend") || queryLower.includes("action") || queryLower.includes("maintenance")) {
      return (
        "### Recommended Maintenance Actions\n\n" +
        "Based on the verified investigation report for **Pump P-102**:\n\n" +
        "1. **Schedule Non-Drive End Bearing Inspection**: Perform high-frequency acoustic demodulation (envelope analysis) within 7 operational days.\n" +
        "2. **Lubricant Sampling & Tribology**: Inspect grease for metallic particulate contamination and thermal oxidation.\n" +
        "3. **Shaft Alignment & Soft Foot Check**: Verify laser coupling alignment with driver motor to rule out angular misalignment.\n" +
        "4. **Operational Monitoring**: Increase vibration monitoring frequency to weekly intervals or set alarm setpoint at 4.0 mm/s RMS."
      );
    }
    return (
      `Regarding your inquiry about **Pump P-102**:\n\n` +
      `The sovereign investigation report indicates an overall status of **Attention Required** (91% confidence). ` +
      `Telemetry recorded vibration climbing from 2.1 mm/s in January to 3.7 mm/s in July, exceeding the 3.0 mm/s advisory limit. ` +
      `Process connectivity confirms downstream reliance by Reactor R-101 via Valve V-204.\n\n` +
      `Feel free to ask about specific findings, evidentiary citations, or recommended corrective workflows.`
    );
  }

  // 2. Attachment-grounded responses
  if (attachments.length > 0) {
    const docNames = attachments.map((a) => a.filename).join(", ");
    const previewTexts = attachments
      .filter((a) => a.extracted_text)
      .map((a) => `**From ${a.filename}**:\n> ${a.extracted_text?.slice(0, 300)}...`)
      .join("\n\n");

    return (
      `### Analysis of Attached Document(s) (${docNames})\n\n` +
      `I have ingested and parsed the uploaded file(s) on-premise without external telemetry:\n\n` +
      (previewTexts ? `${previewTexts}\n\n` : "") +
      `**Response to: "${userQuery}"**\n\n` +
      `Based on the uploaded technical documentation and KavachAI's sovereign engineering knowledge base:\n` +
      `- **Data Integrity**: Verified document format and parameters against plant safety criteria.\n` +
      `- **Relevance Assessment**: The contents align with equipment operational limits and monitoring protocols.\n` +
      `- **Next Step**: You can ask specific questions regarding operating thresholds, maintenance logs, or comparative baselines.`
    );
  }

  // 3. General industrial domain queries
  if (queryLower.includes("bearing") && (queryLower.includes("fail") || queryLower.includes("cause"))) {
    return (
      "### Common Causes of Bearing Failure in Industrial Pumps\n\n" +
      "According to ISO 15243 and industrial plant reliability standards, bearing failure typically stems from:\n\n" +
      "1. **Improper Lubrication (50–60% of cases)**:\n" +
      "   - Under-lubrication causing metal-to-metal contact and thermal seizure.\n" +
      "   - Over-greasing causing fluid friction and churning overheating.\n" +
      "   - Viscosity breakdown due to elevated operating temperature.\n\n" +
      "2. **Contamination (20–25%)**:\n" +
      "   - Ingress of moisture/process fluids resulting in rust or micro-pitting.\n" +
      "   - Particulate contamination causing abrasive 3-body wear.\n\n" +
      "3. **Misalignment & Unbalance (10–15%)**:\n" +
      "   - Angular or parallel shaft misalignment generating cyclic fatigue stresses.\n" +
      "   - Impeller unbalance producing 1X rotational frequency vibration.\n\n" +
      "4. **Electrical Fluting / Stray Currents**:\n" +
      "   - VFD-induced common-mode voltages discharging across the oil film creating EDM washboard patterns.\n\n" +
      "**Diagnostic Action**: Perform high-frequency envelope demodulation and oil ferrography."
    );
  }

  if (queryLower.includes("vibration") && (queryLower.includes("technique") || queryLower.includes("analysis"))) {
    return (
      "### Vibration Analysis Techniques for Rotating Machinery\n\n" +
      "Key diagnostic techniques compliant with **ISO 10816-3 / ISO 20816**:\n\n" +
      "1. **Overall Velocity RMS**: Measures overall energy in the 10 Hz – 1,000 Hz band; primary indicator for unbalance, looseness, and misalignment.\n" +
      "2. **FFT Spectral Analysis**: Decomposes the signal into frequency components:\n" +
      "   - **1X RPM**: Unbalance or bent shaft.\n" +
      "   - **2X RPM**: Misalignment or mechanical looseness.\n" +
      "   - **Vane Pass Frequency (VFX = RPM × Blades)**: Hydraulic cavitation or impeller pass issues.\n" +
      "3. **Time Waveform Analysis (TWF)**: Identifies impacts, truncations, and transient shocks.\n" +
      "4. **Envelope Demodulation (PeakVue / HFE)**: Isolates micro-impact bursts from subsurface bearing spalls at BPFO, BPFI, BSF, and FTF defect frequencies."
    );
  }

  if (queryLower.includes("confined space") || queryLower.includes("ppe")) {
    return (
      "### PPE and Safety Standards for Confined Space Entry\n\n" +
      "Under OSHA 1910.146 and national industrial HSE regulations, permit-required confined space entry requires:\n\n" +
      "1. **Atmospheric Testing (Mandatory 4-Gas Detector)**:\n" +
      "   - **Oxygen**: 19.5% to 23.5%.\n" +
      "   - **Flammability**: < 10% of LEL (Lower Explosive Limit).\n" +
      "   - **Toxics**: H₂S (< 10 ppm) and CO (< 35 ppm).\n\n" +
      "2. **Personal Protective Equipment (PPE)**:\n" +
      "   - Full-body harness with dorsal D-ring attached to a mechanical retrieval winch/tripod.\n" +
      "   - Continuous calibrated multi-gas monitor with visual/audible alarms.\n" +
      "   - Chemical-resistant coveralls (Tychem) and non-sparking footwear.\n" +
      "   - Intrinsically safe communications gear and Class I, Div 1 lighting.\n" +
      "   - Positive-pressure SCBA or SAR if atmospheric hazards exceed permissible exposure limits."
    );
  }

  if (queryLower.includes("iso 13849") || queryLower.includes("safety standard")) {
    return (
      "### Summary of ISO 13849 Safety Standards\n\n" +
      "**ISO 13849-1** governs the functional safety of safety-related parts of control systems (SRP/CS):\n\n" +
      "- **Performance Levels (PL)**: Graded from **PL a** (lowest risk reduction) to **PL e** (highest risk reduction).\n" +
      "- **Key Parameters**:\n" +
      "  1. **Category (Architecture)**: B, 1, 2, 3, or 4 (single channel vs dual redundant with test channel).\n" +
      "  2. **MTTFd (Mean Time to Dangerous Failure)**: Low (3–10 yrs), Medium (10–30 yrs), High (30–100 yrs).\n" +
      "  3. **DCavg (Diagnostic Coverage)**: Fraction of dangerous failures detected by self-diagnostics (None, Low, Medium, High >99%).\n" +
      "  4. **CCF (Common Cause Failure)**: Defenses against simultaneous multiple channel failures (e.g. diversity, physical separation).\n\n" +
      "Plant safety systems must validate that the achieved PL meets or exceeds the required Performance Level (**PLr**)."
    );
  }

  if (queryLower.includes("root cause") || queryLower.includes("rca")) {
    return (
      "### Root Cause Analysis (RCA) for Equipment Failure\n\n" +
      "A structured RCA follows this proven 5-step process:\n\n" +
      "1. **Define the Problem**: Document the failure mode, affected equipment, date/time, and operating conditions at failure.\n" +
      "2. **Gather Evidence**: Collect maintenance records, sensor data, operator logs, photos, vibration spectra, and oil analysis reports.\n" +
      "3. **Map Causal Chain (5-Whys / Fishbone Diagram)**:\n" +
      "   - Categorize causes: *Man, Machine, Method, Material, Measurement, Environment (6M)*.\n" +
      "   - Apply the '5-Whys' to trace each symptom to its root physical, human, or systemic cause.\n" +
      "4. **Verify Root Causes**: Cross-validate each identified root cause with the physical evidence gathered.\n" +
      "5. **Corrective Actions**: Define CAPA (Corrective and Preventive Actions) with owners, due dates, and verification criteria.\n\n" +
      "**KavachAI Integration**: Upload inspection reports, sensor telemetry, and P&ID drawings to let the multi-agent investigation system perform automated RCA."
    );
  }

  if (queryLower.includes("iso 10816") || queryLower.includes("vibration severity")) {
    return (
      "### ISO 10816 / ISO 20816 Vibration Severity Standard\n\n" +
      "**ISO 10816-3** (now superseded by **ISO 20816-3**) defines vibration severity zones for rotating machinery:\n\n" +
      "| Zone | Velocity RMS | Condition |\n" +
      "|------|-------------|-----------|\n" +
      "| **A** | ≤ 2.3 mm/s | New/recently commissioned — Excellent |\n" +
      "| **B** | 2.3 – 4.5 mm/s | Acceptable for long-term continuous operation |\n" +
      "| **C** | 4.5 – 7.1 mm/s | Marginal — monitor closely, plan maintenance |\n" +
      "| **D** | > 7.1 mm/s | Unacceptable — risk of damage, shut down |\n\n" +
      "**Application to Pump P-102**:\n" +
      "- Jan: 2.1 mm/s → Zone A (Acceptable)\n" +
      "- Apr: 2.8 mm/s → Zone B (Acceptable but trending)\n" +
      "- Jul: 3.7 mm/s → Zone B/C boundary (⚠ Advisory threshold per OEM manual: 3.0 mm/s)"
    );
  }

  // Fallback general sovereign industrial answer
  return (
    `**KavachAI Sovereign Industrial Intelligence**\n\n` +
    `Regarding: "${userQuery}"\n\n` +
    `- **System Context**: All data processing is executed on-premise in compliance with sovereign industrial standards.\n` +
    `- **Assessment**: Industrial assets must adhere to preventive maintenance baselines, OEM operational tolerances, and regular vibration/thermal monitoring.\n` +
    `- **Assistance**: You can request specific telemetry calculations, ask follow-up safety questions, or upload inspection reports and P&IDs for automated extraction.`
  );
}

