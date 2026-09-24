"use client";
import Link from "next/link";
import { useNetworkMonitor } from "@/app/hooks/useNetworkMonitor";
export default function NetworkStatusPill({ className="" }: {compact?:boolean;className?:string}) {
 const {report} = useNetworkMonitor();
 return <Link href="/network-monitor" className={`text-xs border rounded-full px-3 py-1 ${className}`}>
  {report ? `Backend: ${report.external_recorded} blocked attempts` : "Network status unknown"}
 </Link>;
}
