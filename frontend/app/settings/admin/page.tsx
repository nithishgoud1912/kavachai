"use client";
import AppShell from "@/app/components/AppShell";
import AdminGuard from "@/app/components/AdminGuard";
export default function AdminSettingsPage() {
 return <AppShell title="Deployment policy" subtitle="Server-managed settings"><AdminGuard>
  <section className="p-6 space-y-4"><h2>Sandbox and retention policy</h2>
  <p>Resource limits are managed on the server. Browser changes do not alter container security.</p>
  <p>The sandbox enforces no network, a read-only root, a non-root user, 256 MB memory, one CPU, 64 processes and bounded output. Execution time is limited to 60 seconds.</p>
  <p>Audit events use a local hash chain. Immutable off-host retention and deployment network verification must be configured by the organization.</p>
  <a href="/model-router">Manage installed model routing</a></section>
 </AdminGuard></AppShell>;
}
