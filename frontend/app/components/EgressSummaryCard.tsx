"use client";
import type { EgressReport } from "@/app/types";
import { downloadJson } from "@/app/services/fileDownload";
export default function EgressSummaryCard({ report, className="" }: {report:EgressReport|null; className?:string}) {
  return <section className={`p-6 rounded-2xl border ${className}`}>
    <h2>Network observations</h2>
    <p>{report ? `${report.total_connections} backend socket events; ${report.external_recorded} disallowed attempts.` : "Network observer unavailable."}</p>
    <p>Air-gap verification is not established. These observations cover the Python backend only. Use an independent network capture for the complete deployment.</p>
    <button disabled={!report} onClick={() => downloadJson("backend-network-observations.json", {report, exported_at:new Date().toISOString()})}>Export observations</button>
  </section>;
}
